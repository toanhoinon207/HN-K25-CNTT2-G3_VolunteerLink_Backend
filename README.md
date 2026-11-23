# VolunteerLink — Backend API (FastAPI + MySQL)

Hệ thống API cho nền tảng **VolunteerLink** (Cổng kết nối Tình nguyện viên & Hoạt động xã hội), xây dựng bằng **FastAPI**, **SQLAlchemy**, **PyMySQL** và **MySQL 8**.

---

## 1. Tính năng chính

- **Xác thực & phân quyền JWT (`USER`, `ORGANIZER`, `ADMIN`)**: Đăng ký, đăng nhập, làm mới token (`refresh`), đăng xuất (`auth_sessions`), quên/đặt lại mật khẩu qua email (SMTP).
- **Hồ sơ cá nhân & Tình nguyện viên**: Cập nhật thông tin cá nhân, kỹ năng, khu vực, đổi mật khẩu, tải lên ảnh đại diện (`/uploads/avatars`).
- **Tổ chức (`Organizations`)**: Đăng ký hồ sơ tổ chức kèm tài liệu pháp lý; Admin xét duyệt (`APPROVED` / `REJECTED`) và tự động nâng quyền tài khoản thành `ORGANIZER`.
- **Chiến dịch (`Campaigns`)**: Tạo bản nháp (`DRAFT`), tải ảnh chiến dịch (`/uploads/campaigns`), gửi duyệt (`PENDING`), Admin phê duyệt mở tuyển (`OPEN`), đồng bộ vòng đời chiến dịch tự động theo thời gian.
- **Đăng ký & Hàng chờ (`Registrations` & `Waitlist`)**: Đăng ký tham gia, hủy đăng ký, duyệt/từ chối đơn, tự động mời từ danh sách chờ và hết hạn lời mời sau 24 giờ.
- **Điểm danh & Khiếu nại (`Attendances` & `Attendance Appeals`)**: Phát mã điểm danh, check-in / check-out theo mã, khiếu nại điểm danh lên Tổ chức hoặc leo thang lên Admin.
- **Xác nhận giờ & Chứng chỉ (`Hour Claims` & `Certificates`)**: Khiếu nại/xác nhận giờ tình nguyện phát sinh, cấp chứng chỉ điện tử, tra cứu xác thực công khai theo mã chứng chỉ và thu hồi chứng chỉ (Admin).
- **Thông báo & Quản trị (`Notifications`, `Admin`, `User Moderation`)**: Thông báo người dùng, thống kê hệ thống, khóa/mở khóa tài khoản kèm lịch sử kiểm duyệt.
- **Tài liệu API tự động (Swagger UI)**: `http://127.0.0.1:8000/docs`.

---

## 2. Yêu cầu môi trường

| Phần mềm | Ghi chú |
|---|---|
| Python **3.10 trở lên** | Khuyến nghị 3.10–3.12 (Windows: tick **Add python.exe to PATH** khi cài) |
| MySQL Server 8 + MySQL Workbench | Hỗ trợ `utf8mb4` để lưu tiếng Việt chuẩn |

---

## 3. Cấu trúc thư mục

```text
HN-K25-CNTT2-G3_VolunteerLink_Backend/
├── app/
│   ├── main.py                  # Khởi tạo FastAPI, lifespan (DB/seed/background task), CORS, mount /uploads, gắn routers
│   ├── core/
│   │   ├── config.py            # Đọc cấu hình từ .env (DB, JWT, CORS, SMTP, AUTO_SEED_ON_STARTUP)
│   │   └── security.py          # Hash mật khẩu (bcrypt) & tạo/giải mã JWT
│   ├── db/
│   │   ├── session.py           # Kết nối MySQL (SQLAlchemy Engine, Base, SessionLocal, get_db)
│   │   └── seed.py              # Tự động nạp sql/seed_all.sql khi bảng users còn trống
│   ├── dependencies/
│   │   └── auth.py              # Dependency lấy current_user và kiểm tra vai trò
│   ├── models/                  # SQLAlchemy ORM models (users, organizations, campaigns, registrations, ...)
│   ├── schemas/                 # Pydantic schemas kiểm tra dữ liệu vào/ra
│   ├── services/                # Tầng xử lý nghiệp vụ & tác vụ đồng bộ nền
│   └── routers/                 # Định nghĩa các endpoint API (/api/...)
├── sql/
│   ├── init.sql                 # Tạo database volunteerlink_db (utf8mb4)
│   ├── seed_all.sql             # Dữ liệu mẫu đầy đủ (users, organizations, campaigns, registrations, ...)
│   └── *.sql                    # Các script migration bổ sung theo từng module
├── uploads/                     # Thư mục lưu file upload (avatars/, campaigns/), tự tạo nếu chưa có
├── requirements.txt             # Danh sách thư viện Python
└── .env.example                 # Mẫu file cấu hình môi trường
```

---

## 4. Cài đặt & Chạy server

### Bước 1: Tạo database MySQL
1. Mở **MySQL Workbench** và kết nối tới MySQL Server (ví dụ `127.0.0.1:3306`).
2. Chạy file `sql/init.sql` (**File → Open SQL Script...** → chọn `sql/init.sql` → bấm **Execute ⚡**) để tạo database `volunteerlink_db` với charset `utf8mb4`.
   > Nếu cần nạp thủ công dữ liệu mẫu, có thể mở và chạy thêm `sql/seed_all.sql`; mặc định backend sẽ tự chạy file này ở lần khởi động đầu tiên khi bảng `users` chưa có dữ liệu (`AUTO_SEED_ON_STARTUP=true`).

### Bước 2: Tạo file cấu hình `.env`
Mở terminal tại thư mục gốc backend:

```bash
# Windows
copy .env.example .env
# Mac / Linux
cp .env.example .env
```

Mở `.env` và cập nhật thông tin phù hợp với máy của bạn:

```env
APP_NAME=Volunteer Link

# MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mat_khau_mysql_cua_ban
DB_NAME=volunteerlink_db

# JWT
JWT_SECRET_KEY=thay_bang_chuoi_bi_mat_cua_ban
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (nhiều origin cách nhau bằng dấu phẩy, hoặc "*" khi dev)
CORS_ORIGINS=*

# SMTP (tùy chọn - dùng cho tính năng quên mật khẩu qua email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
FRONTEND_BASE_URL=http://127.0.0.1:5500
PASSWORD_RESET_EXPIRE_MINUTES=15
```

### Bước 3: Tạo môi trường ảo & cài thư viện

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
- **Windows CMD:** `.venv\Scripts\activate.bat`
- **Mac / Linux:** `source .venv/bin/activate`

Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

### Bước 4: Khởi chạy Backend

```bash
uvicorn app.main:app --reload
```

Khi khởi động thành công, terminal sẽ hiển thị:
- `[DB] Đã kết nối MySQL 127.0.0.1:3306/volunteerlink_db`
- `[SEED] Đã nạp dữ liệu mẫu từ sql/seed_all.sql thành công.` (nếu bảng `users` đang trống)

Kiểm tra nhanh:
- Health check: `http://127.0.0.1:8000/api/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## 5. Tài khoản mẫu (từ `sql/seed_all.sql`)

| Vai trò | Email | Mật khẩu |
|---|---|---|
| `ADMIN` | `admin@gmail.com` | `12345678` |
| `ORGANIZER` | `organizer@gmail.com` | `12345678` |
| `USER` | `user@gmail.com` | `12345678` |

*(Ngoài ra trong `sql/seed_all.sql` còn có thêm các tài khoản `organizer2..5@gmail.com`, `user2..5@gmail.com` và `locked_user@gmail.com` để kiểm thử các trạng thái nghiệp vụ.)*

---

## 6. Tổng hợp nhóm API (`/api`)

| Nhóm Router | Prefix | Chức năng chính |
|---|---|---|
| **Health** | `/api/health` | Kiểm tra trạng thái server & kết nối MySQL |
| **Auth** | `/api/auth` | Đăng ký, đăng nhập, `/me`, refresh token, đăng xuất, quên/đặt lại mật khẩu |
| **Profile** | `/api/profile` | Xem/sửa hồ sơ cá nhân, hồ sơ TNV, upload avatar, đổi mật khẩu |
| **Organizations** | `/api/organizations`, `/api/admin/organizations` | Nộp hồ sơ tổ chức, xem/sửa thông tin tổ chức, thống kê, Admin duyệt tổ chức |
| **Campaigns** | `/api/campaigns`, `/api/admin/campaigns` | Tạo/sửa/gửi duyệt chiến dịch, upload ảnh, danh sách công khai & chi tiết, Admin kiểm duyệt |
| **Registrations** | `/api/registrations` | Đăng ký tham gia, hủy đăng ký, xem đơn của tôi/theo chiến dịch, duyệt/từ chối đơn |
| **Waitlist** | `/api/waitlist` | Tham gia hàng chờ, xem vị trí hàng chờ, phản hồi lời mời tham gia |
| **Attendances** | `/api/attendances` | Tạo & xem mã điểm danh, check-in / check-out, lịch sử điểm danh |
| **Attendance Appeals** | `/api/attendance-appeals` | Gửi khiếu nại điểm danh, Tổ chức xét duyệt, leo thang & Admin xử lý |
| **Hour Claims** | `/api/hour-claims` | Gửi yêu cầu xác nhận giờ phát sinh, Tổ chức/Admin duyệt giờ |
| **Certificates** | `/api/certificates` | Xem chứng chỉ của tôi, danh sách đủ điều kiện, cấp chứng chỉ, xác thực công khai theo mã |
| **Notifications** | `/api/notifications` | Lấy danh sách thông báo, số chưa đọc, đánh dấu đã đọc |
| **Admin & Moderation** | `/api/admin`, `/api/admin/users` | Thống kê dashboard, quản lý user/role/status, khóa/mở khóa tài khoản, thu hồi chứng chỉ |

> Tất cả các endpoint yêu cầu đăng nhập sử dụng header `Authorization: Bearer <access_token>`. Chi tiết request/response xem trực tiếp tại `/docs`.

---

## 7. Lưu ý vận hành & Xử lý lỗi thường gặp

- **Tác vụ nền (Background Task)**: Khi server chạy, `lifespan` trong `app/main.py` chạy tác vụ nền mỗi 30 giây để cập nhật trạng thái vòng đời chiến dịch và hết hạn lời mời waitlist quá 24 giờ.
- **Static uploads**: Ảnh đại diện và ảnh chiến dịch lưu tại thư mục `uploads/` và phục vụ qua URL `http://127.0.0.1:8000/uploads/...`.

| Lỗi thường gặp | Nguyên nhân & Cách xử lý |
|---|---|
| `Unknown database 'volunteerlink_db'` | Chưa chạy `sql/init.sql` trong MySQL Workbench |
| `Access denied for user 'root'@'localhost'` | Sai `DB_USER` hoặc `DB_PASSWORD` trong file `.env` |
| `Can't connect to MySQL server on '127.0.0.1'` | Dịch vụ MySQL chưa bật (Windows: mở **Services** → start **MySQL80**) hoặc sai `DB_PORT` |
| `ModuleNotFoundError: No module named 'fastapi'` | Chưa kích hoạt `.venv` hoặc chưa chạy `pip install -r requirements.txt` |
| Lỗi CORS khi Frontend gọi API | Kiểm tra `CORS_ORIGINS` trong `.env` (ví dụ `CORS_ORIGINS=*` khi dev) và khởi động lại `uvicorn` |
