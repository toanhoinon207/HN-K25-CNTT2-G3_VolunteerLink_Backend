from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.users import UserModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel


class AdminDashboardService:

    @staticmethod
    def get_admin_dashboard_stats(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        # 1. Tài khoản (tổng, phân theo role, chi tiết từng tài khoản)
        users = db.query(UserModel).all()
        accounts_by_role = {}
        account_details = []

        for u in users:
            role_raw = getattr(u, "role", "USER")
            role_val = role_raw.value if hasattr(role_raw, "value") else str(role_raw)
            accounts_by_role[role_val] = accounts_by_role.get(role_val, 0) + 1
            account_details.append({
                "id": u.id,
                "full_name": getattr(u, "full_name", getattr(u, "username", f"User #{u.id}")),
                "email": getattr(u, "email", None),
                "role": role_val,
                "is_active": getattr(u, "is_active", True),
            })

        # 2. Tổ chức (tổng và chi tiết)
        organization_details = []
        try:
            from app.models.organizations import OrganizationModel
            orgs = db.query(OrganizationModel).all()
            total_organizations = len(orgs)
            for org in orgs:
                org_status_raw = getattr(org, "status", None)
                org_status = org_status_raw.value if hasattr(org_status_raw, "value") else (
                    str(org_status_raw) if org_status_raw is not None else None
                )
                organization_details.append({
                    "id": org.id,
                    "name": getattr(org, "name", getattr(org, "title", f"Organization #{org.id}")),
                    "email": getattr(org, "email", None),
                    "phone": getattr(org, "phone", None),
                    "status": org_status,
                })
        except Exception:
            org_users = [
                u for u in users
                if str(getattr(u, "role", "")).lower() == "organizer"
            ]
            total_organizations = len(org_users)
            for u in org_users:
                organization_details.append({
                    "id": u.id,
                    "name": getattr(u, "full_name", getattr(u, "email", f"Organizer #{u.id}")),
                    "email": getattr(u, "email", None),
                })

        # 3. Chiến dịch theo khoảng thời gian (dựa trên start_time)
        campaign_query = db.query(CampaignModel)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            campaign_query = campaign_query.filter(CampaignModel.start_time >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            campaign_query = campaign_query.filter(CampaignModel.start_time <= end_dt)

        campaigns = campaign_query.all()
        campaign_ids = [c.id for c in campaigns]

        campaigns_by_status = {}
        campaigns_by_month = {}
        campaign_details = []

        minutes_by_campaign = {}
        sessions_by_campaign = {}

        if campaign_ids:
            rows = db.query(
                RegistrationModel.campaign_id,
                func.sum(AttendanceModel.total_minutes).label("total_minutes"),
                func.count(AttendanceModel.id).label("total_sessions")
            ).join(
                AttendanceModel, AttendanceModel.registration_id == RegistrationModel.id
            ).filter(
                RegistrationModel.campaign_id.in_(campaign_ids)
            ).group_by(RegistrationModel.campaign_id).all()

            for r in rows:
                minutes_by_campaign[r.campaign_id] = int(r.total_minutes or 0)
                sessions_by_campaign[r.campaign_id] = int(r.total_sessions or 0)

        for c in campaigns:
            status_raw = getattr(c, "status", "UNKNOWN")
            status_val = status_raw.value if hasattr(status_raw, "value") else str(status_raw)
            campaigns_by_status[status_val] = campaigns_by_status.get(status_val, 0) + 1

            month_key = None
            if getattr(c, "start_time", None):
                month_key = c.start_time.strftime("%Y-%m")
                campaigns_by_month[month_key] = campaigns_by_month.get(month_key, 0) + 1

            c_minutes = minutes_by_campaign.get(c.id, 0)
            c_hours = round(c_minutes / 60.0, 2)

            start_val = getattr(c, "start_time", None)
            end_val = getattr(c, "end_time", None)

            campaign_details.append({
                "id": c.id,
                "title": getattr(c, "title", getattr(c, "name", f"Campaign #{c.id}")),
                "status": status_val,
                "month": month_key,
                "start_time": start_val.isoformat() if hasattr(start_val, "isoformat") else (str(start_val) if start_val else None),
                "end_time": end_val.isoformat() if hasattr(end_val, "isoformat") else (str(end_val) if end_val else None),
                "organization_id": getattr(c, "organization_id", None),
                "contributed_minutes": c_minutes,
                "contributed_hours": c_hours,
                "attendance_sessions": sessions_by_campaign.get(c.id, 0),
            })

        campaigns_by_month = dict(sorted(campaigns_by_month.items()))

        # 4. Tổng giờ đóng góp và chi tiết theo chiến dịch
        total_minutes = sum(minutes_by_campaign.values())
        total_contributed_hours = round(total_minutes / 60.0, 2)

        hours_by_campaign = [
            {
                "campaign_id": item["id"],
                "campaign_title": item["title"],
                "total_minutes": item["contributed_minutes"],
                "total_hours": item["contributed_hours"],
                "attendance_sessions": item["attendance_sessions"],
            }
            for item in campaign_details
        ]

        # 5. Chứng nhận đã cấp và chi tiết
        certificate_details = []
        total_certificates = 0
        active_certificates = 0
        revoked_certificates = 0

        try:
            from app.models.certificate import CertificateModel
            cert_query = db.query(CertificateModel)

            if start_date and hasattr(CertificateModel, "issued_at"):
                start_dt = datetime.combine(start_date, datetime.min.time())
                cert_query = cert_query.filter(CertificateModel.issued_at >= start_dt)
            elif start_date and hasattr(CertificateModel, "campaign_id"):
                cert_query = (
                    cert_query.filter(CertificateModel.campaign_id.in_(campaign_ids))
                    if campaign_ids else None
                )

            if end_date and cert_query is not None and hasattr(CertificateModel, "issued_at"):
                end_dt = datetime.combine(end_date, datetime.max.time())
                cert_query = cert_query.filter(CertificateModel.issued_at <= end_dt)
            elif end_date and cert_query is not None and hasattr(CertificateModel, "campaign_id"):
                cert_query = (
                    cert_query.filter(CertificateModel.campaign_id.in_(campaign_ids))
                    if campaign_ids else None
                )

            certs = cert_query.all() if cert_query is not None else []
            total_certificates = len(certs)

            for cert in certs:
                status_raw = getattr(cert, "status", "ACTIVE")
                status_val = status_raw.value if hasattr(status_raw, "value") else str(status_raw)
                if status_val.upper() == "ACTIVE":
                    active_certificates += 1
                elif status_val.upper() == "REVOKED":
                    revoked_certificates += 1

                hours_val = getattr(cert, "total_hours", 0)
                issued_val = getattr(cert, "issued_at", None)

                certificate_details.append({
                    "id": cert.id,
                    "certificate_code": getattr(cert, "certificate_code", None),
                    "user_id": getattr(cert, "user_id", None),
                    "campaign_id": getattr(cert, "campaign_id", None),
                    "total_hours": float(hours_val) if hours_val is not None else 0.0,
                    "status": status_val,
                    "revoked_reason": getattr(cert, "revoked_reason", None),
                    "issued_at": issued_val.isoformat() if hasattr(issued_val, "isoformat") else (str(issued_val) if issued_val else None),
                })
        except Exception:
            total_certificates = 0
            active_certificates = 0
            revoked_certificates = 0
            certificate_details = []

        return {
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "accounts": {
                "total": len(users),
                "by_role": accounts_by_role,
                "items": account_details,
            },
            "organizations": {
                "total": total_organizations,
                "items": organization_details,
            },
            "campaigns": {
                "total": len(campaigns),
                "by_status": campaigns_by_status,
                "by_month": campaigns_by_month,
                "items": campaign_details,
            },
            "contributed_hours": {
                "total_minutes": total_minutes,
                "total_hours": total_contributed_hours,
                "by_campaign": hours_by_campaign,
            },
            "certificates": {
                "total": total_certificates,
                "total_issued": active_certificates,
                "total_revoked": revoked_certificates,
                "items": certificate_details,
            },
        }