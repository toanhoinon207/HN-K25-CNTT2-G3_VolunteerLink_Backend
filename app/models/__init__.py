# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
from app.models.item import Item  # noqa: F401
<<<<<<< HEAD
from app.models.campaigns import CampaignModel
=======
from app.models.attendances import AttendanceModel
from app.models.certificate import CertificateModel
from app.models.hourclaims import HourClaimModel
from app.models.campaigns import CampaignModel
 
>>>>>>> 11d3b787a7df218588b8111e8d105f211e16e236
