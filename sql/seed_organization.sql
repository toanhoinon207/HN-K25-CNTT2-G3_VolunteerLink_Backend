USE volunteerlink_db;

INSERT INTO organizations (
    id, name, description, logo_url, address, email, phone, document_url, status, owner_id, rejection_reason, created_at, updated_at
) VALUES 
(
    1,
    'Quỹ Tình nguyện Xanh Việt Nam', 
    'Tổ chức phi lợi nhuận hoạt động vì môi trường, chuyên tổ chức các chiến dịch dọn rác, trồng cây gây rừng và bảo vệ nguồn nước sạch.', 
    'https://cdn.example.com/logos/xanh_vietnam.png', 
    'Số 15 phố Huế, Phường Hàng Bài, Quận Hoàn Kiếm, Hà Nội', 
    'contact@xanhvietnam.org', 
    '02438251234', 
    'https://cdn.example.com/documents/giay_phep_xanh_vn.pdf', 
    'APPROVED', 
    3, 
    NULL,
    '2026-11-01 09:00:00',
    '2026-11-01 09:00:00'
),
(
    2,
    'Câu lạc bộ Mùa Hè Xanh TP.HCM', 
    'Tổ chức tình nguyện thanh niên hỗ trợ các hoạt động cộng đồng, dạy học miễn phí cho trẻ em vùng cao và cứu trợ thiên tai.', 
    'https://cdn.example.com/logos/mua_he_xanh.png', 
    'Nhà Văn hóa Thanh niên, số 4 Phạm Ngọc Thạch, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh', 
    'muahexanh@tphcm.gov.vn', 
    '02838294444', 
    'https://cdn.example.com/documents/quyet_dinh_mhx.pdf', 
    'APPROVED', 
    4, 
    NULL,
    '2026-11-01 09:00:00',
    '2026-11-01 09:00:00'
),
(
    3,
    'Trung tâm Thiện nguyện Ánh Sáng', 
    'Chuyên kết nối các nhà hảo tâm thực hiện các chương trình phát cơm từ thiện tại bệnh viện và xây nhà tình thương.', 
    'https://cdn.example.com/logos/anh_sang.png', 
    '102 Nguyễn Chí Thanh, Phường Láng Hạ, Quận Đống Đa, Hà Nội', 
    'info@anhsangcharity.vn', 
    '0902333444', 
    'https://cdn.example.com/documents/giay_chung_nhan_anh_sang.pdf', 
    'APPROVED', 
    5, 
    NULL,
    '2026-11-01 09:00:00',
    '2026-11-01 09:00:00'
),
(
    4,
    'Ánh Sáng Tri Thức',
    'Tổ chức các chương trình giáo dục cộng đồng và trao học bổng cho học sinh nghèo vượt khó.',
    'https://cdn.example.com/logos/anh_sang_tri_thuc.png',
    'Thanh Xuân, Hà Nội',
    'contact@anhsangtrithuc.vn',
    '0244567890',
    'https://cdn.example.com/documents/ho_so_astt.pdf',
    'PENDING',
    6,
    NULL,
    '2026-11-02 09:00:00',
    '2026-11-02 09:00:00'
),
(
    5,
    'Nhịp Cầu Nhân Ái',
    'Tổ chức các chương trình thiện nguyện và hỗ trợ cộng đồng vùng sâu vùng xa.',
    'https://cdn.example.com/logos/nhip_cau_nhan_ai.png',
    'Long Biên, Hà Nội',
    'contact@nhipcaunhanai.vn',
    '0245678901',
    'https://cdn.example.com/documents/ho_so_ncna.pdf',
    'REJECTED',
    7,
    'Hồ sơ chưa đáp ứng yêu cầu xác minh.',
    '2026-11-02 09:00:00',
    '2026-11-02 09:00:00'
);
