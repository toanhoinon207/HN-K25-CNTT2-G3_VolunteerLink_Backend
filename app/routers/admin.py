
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/certificates")
def list_all_certificates(
    cert_status: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Lấy toàn bộ danh sách chứng chỉ đã cấp trong hệ thống."""
    query = (
        db.query(
            CertificateModel,
            UserModel.full_name.label("user_name"),
            UserModel.email.label("user_email"),
            CampaignModel.title.label("campaign_title"),
        )
        .join(UserModel, UserModel.id == CertificateModel.user_id)
        .join(CampaignModel, CampaignModel.id == CertificateModel.campaign_id)
    )
    if cert_status and cert_status.upper() in {"ACTIVE", "REVOKED"}:
        query = query.filter(CertificateModel.status == cert_status.upper())

    rows = query.order_by(CertificateModel.id.desc()).all()
    return [
        {
            "id": cert.id,
            "certificate_code": cert.certificate_code,
            "user_id": cert.user_id,
            "user_name": user_name,
            "user_email": user_email,
            "campaign_id": cert.campaign_id,
            "campaign_title": campaign_title,
            "total_hours": float(cert.total_hours),
            "issued_at": cert.issued_at,
            "status": cert.status,
            "revoked_reason": cert.revoked_reason,
        }
        for cert, user_name, user_email, campaign_title in rows
    ]


@router.patch("/certificates/{cert_id}/revoke")
def revoke_certificate(
    cert_id: int,
    payload: AdminCertificateRevokeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Thu hồi chứng chỉ tình nguyện viên kèm lý do."""
    cert = db.query(CertificateModel).filter(CertificateModel.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy chứng chỉ.",
        )

    if cert.status == "REVOKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chứng chỉ này đã bị thu hồi trước đó.",
        )

    reason = payload.reason.strip()
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập lý do thu hồi chứng chỉ.",
        )

    cert.status = "REVOKED"
    cert.revoked_reason = reason
    create_notification(
        db=db,
        user_id=cert.user_id,
        title="Chứng chỉ đã bị thu hồi",
        content=f"Chứng chỉ mã {cert.certificate_code} đã bị thu hồi. Lý do: {reason}",
        link="user-dashboard.html?tab=certificates",
    )
    db.commit()
    db.refresh(cert)

    return {
        "id": cert.id,
        "certificate_code": cert.certificate_code,
        "status": cert.status,
        "revoked_reason": cert.revoked_reason,
    }


@router.get("/dashboard/stats")
def get_admin_dashboard_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Thống kê Dashboard cho quản trị viên."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày bắt đầu không được sau ngày kết thúc.",
        )

    stats = AdminDashboardService.get_admin_dashboard_stats(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
    return {"message": "Thành công", "data": stats}
