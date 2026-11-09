# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
from app.models.item import Item  # noqa: F401

from app.models.campaigns import CampaignModel

from app.models.attendances import AttendanceModel
from app.models.certificate import CertificateModel
from app.models.hourclaims import HourClaimModel
from app.models.campaigns import CampaignModel
from app.models.registration import RegistrationModel
from app.models.waitlist_entry import WaitlistEntryModel
 
