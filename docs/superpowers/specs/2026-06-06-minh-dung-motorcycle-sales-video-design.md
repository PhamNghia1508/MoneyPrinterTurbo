# Thiết Kế Công Cụ Tạo Video Bán Xe Máy Minh Dũng

## 1. Mục tiêu

Tùy biến MoneyPrinterTurbo thành công cụ tạo video dọc bán xe máy cũ thanh lý cho cửa hàng Minh Dũng. Video cần giữ người xem ngay trong 1-3 giây đầu, cung cấp đủ thông tin để tạo niềm tin và thúc đẩy khách gọi điện, nhắn Zalo hoặc đến cửa hàng xem xe.

Kênh sử dụng chính:

- TikTok
- Facebook Reels

Thông tin thương hiệu cố định:

- Cửa hàng: Minh Dũng
- Điện thoại/Zalo: 0902 143 241
- Địa chỉ: 08 Quang Trung, TP. Quảng Ngãi

## 2. Phạm vi phiên bản đầu

Phiên bản đầu tập trung vào một quy trình duy nhất: tạo video bán từng chiếc xe đang có tại cửa hàng.

Bao gồm:

- Form nhập dữ liệu xe chuyên dụng.
- Sinh kịch bản tiếng Việt dài khoảng 35-45 giây.
- Giọng văn hóm hỉnh vừa phải, gần gũi nhưng đáng tin.
- Hook bán hàng trong 1-3 giây đầu.
- Upload và ghép ảnh/video xe theo thứ tự người dùng chọn.
- Cho phép sửa kịch bản trước khi dựng video.
- Sinh caption và hashtag cho TikTok và Facebook Reels.
- Lưu sẵn thông tin liên hệ của cửa hàng.

Chưa bao gồm:

- Quản lý kho xe.
- Đăng video tự động lên mạng xã hội.
- Chatbot tư vấn khách hàng.
- Tự nhận dạng thông số xe từ hình ảnh.
- Các chế độ nội dung so sánh xe hoặc bắt trend độc lập.

## 3. Dữ liệu đầu vào

Form "Tạo video bán xe" thu thập:

- Tên xe, bắt buộc.
- Đời xe, bắt buộc.
- ODO, có thể đánh dấu "chưa xác minh" hoặc "không công bố".
- Biển số, có thể ẩn một phần khi lên nội dung.
- Giá bán, có thể chọn đọc trực tiếp hoặc kêu gọi liên hệ để nhận giá.
- Tình trạng thực tế, bắt buộc.
- Ưu điểm nổi bật, bắt buộc ít nhất một ý.
- Hồ sơ pháp lý và khả năng sang tên.
- Ghi chú bổ sung dành cho AI.
- Danh sách ảnh/video tải lên.

Hồ sơ pháp lý mặc định là đầy đủ và có hỗ trợ sang tên, nhưng người dùng vẫn có thể sửa cho từng xe.

## 4. Cấu trúc kịch bản

Kịch bản mục tiêu dài khoảng 90-120 từ, phù hợp tốc độ đọc tự nhiên trong 35-45 giây.

### 4.1. Hook 1-3 giây

Mở đầu phải tạo tò mò hoặc nêu ngay lợi ích đáng chú ý. Hook thay đổi theo dữ liệu xe và không lặp máy móc các cụm như "siêu phẩm" hoặc "cực phẩm".

Ví dụ:

> Tầm tiền này mà kiếm được em xe giấy tờ đủ như thế này thì hơi khó đấy nha!

### 4.2. Giới thiệu xe

Nêu tên xe, đời xe và lý do chiếc xe phù hợp với người mua. Cách diễn đạt linh hoạt theo từng loại xe, thay vì giả định mọi khách hàng có cùng nhu cầu.

### 4.3. Tình trạng và giá trị thực tế

Trình bày ODO, tình trạng, ưu điểm và các điểm cần lưu ý bằng ngôn ngữ dễ hiểu. Nội dung chỉ được dùng dữ liệu người dùng đã nhập.

### 4.4. Tạo niềm tin

Nhấn mạnh hồ sơ pháp lý đầy đủ và hỗ trợ sang tên. Không mô tả xe là "zin", ODO chuẩn, chưa đâm đụng, máy nguyên bản hoặc dùng các khẳng định tương tự nếu dữ liệu đầu vào không xác nhận.

### 4.5. Giá và CTA

Nếu bật công khai giá, đọc giá rõ ràng. Nếu ẩn giá, sử dụng lời kêu gọi liên hệ hợp lý, không dùng chiêu gây hiểu lầm.

CTA kết thúc phải chứa:

- Minh Dũng.
- 0902 143 241.
- 08 Quang Trung, TP. Quảng Ngãi.

CTA có thể thay đổi cách diễn đạt để các video không giống hệt nhau.

## 5. Giọng thương hiệu

Giọng đọc và câu chữ:

- Hóm hỉnh vừa phải.
- Gần gũi với người mua xe tại Việt Nam.
- Nhanh, rõ và có năng lượng nhưng không la hét liên tục.
- Tập trung vào lợi ích thật, hồ sơ pháp lý và lời mời xem xe.
- Không chế giễu khách hàng hoặc đối thủ.
- Không tạo khan hiếm giả.
- Không dùng biệt ngữ như "zin đét", "xe cọp" nếu chưa có dữ liệu xác nhận.

Mục tiêu là khiến người xem cảm thấy video vui, dễ nghe và cửa hàng đáng tin.

## 6. WebUI

WebUI giữ pipeline hiện tại nhưng bổ sung chế độ chuyên dụng "Bán xe Minh Dũng".

Chế độ này:

- Hiển thị form dữ liệu xe thay cho ô chủ đề chung chung.
- Điền sẵn video dọc 9:16.
- Chọn nguồn tư liệu local.
- Ghép tư liệu theo thứ tự upload.
- Dùng clip ngắn khoảng 2-3 giây để duy trì nhịp.
- Đặt thời lượng mục tiêu 35-45 giây.
- Điền sẵn phong cách kịch bản và thông tin cửa hàng.
- Cho phép xem và sửa kịch bản trước khi bấm tạo video.
- Cho phép chọn công khai hoặc ẩn giá cho từng xe.

Các cài đặt kỹ thuật nâng cao hiện có vẫn được giữ trong phần mở rộng, để không làm mất khả năng tùy chỉnh của MoneyPrinterTurbo.

## 7. Xử lý tư liệu

Ảnh và video local được giữ theo thứ tự upload. Tư liệu đầu tiên được xem là cảnh mở đầu do người dùng chủ động chọn.

Ứng dụng sẽ:

- Yêu cầu ít nhất một ảnh hoặc video hợp lệ.
- Giữ thứ tự tuần tự thay vì xáo trộn.
- Ưu tiên clip ngắn 2-3 giây.
- Cho phép dùng cả ảnh và video trong cùng một tác vụ.
- Không tự kết luận tình trạng xe từ hình ảnh.

Phiên bản đầu không tự chấm điểm cảnh đẹp nhất. Người dùng chịu trách nhiệm đặt cảnh hook ở vị trí đầu tiên, giúp kết quả dễ đoán và tránh thêm một hệ thống nhận diện hình ảnh chưa cần thiết.

## 8. Sinh caption và hashtag

Sau khi có kịch bản, ứng dụng sinh metadata riêng cho:

- TikTok.
- Facebook Reels.

Caption phải ngắn gọn, chứa thông tin chính của xe và lời kêu gọi liên hệ. Hashtag ưu tiên từ khóa liên quan đến mẫu xe, xe máy cũ, xe thanh lý và khu vực Quảng Ngãi; không nhồi hashtag không liên quan.

Người dùng được xem và chỉnh sửa caption trước khi sử dụng. Ứng dụng không tự đăng nội dung lên nền tảng.

## 9. Kiểm tra dữ liệu và xử lý lỗi

Trước khi sinh kịch bản:

- Chặn tác vụ nếu thiếu tên xe, đời xe, tình trạng hoặc ưu điểm.
- Cảnh báo nhưng không chặn nếu thiếu ODO, giá hoặc biển số.
- Yêu cầu người dùng chọn rõ công khai giá hay liên hệ nhận giá.
- Không gửi trường trống cho AI dưới dạng một sự thật.

Sau khi sinh kịch bản:

- Kiểm tra có hook, thông tin pháp lý và CTA.
- Kiểm tra kịch bản không xuất hiện khẳng định bị cấm nếu đầu vào không có.
- Cảnh báo nếu độ dài nằm ngoài khoảng mục tiêu.
- Luôn cho phép người dùng chỉnh sửa trước khi dựng video.

Nếu LLM thất bại, WebUI hiển thị lỗi dễ hiểu và giữ nguyên dữ liệu form để người dùng thử lại.

## 10. Kiến trúc thay đổi

Các trách nhiệm được tách như sau:

- Một model dữ liệu xe định nghĩa các trường và quy tắc kiểm tra.
- Một module prompt chuyên dựng ngữ cảnh bán xe và kiểm tra kịch bản.
- Dịch vụ LLM hiện tại tiếp tục chịu trách nhiệm gọi nhà cung cấp AI.
- WebUI thu thập dữ liệu, hiển thị cảnh báo và chuyển dữ liệu vào module prompt.
- Pipeline video hiện tại tiếp tục xử lý TTS, phụ đề và ghép tư liệu.
- Dịch vụ social metadata hiện tại được tái sử dụng và bổ sung ngữ cảnh cửa hàng.

Prompt bán xe không thay thế hoàn toàn prompt tổng quát của MoneyPrinterTurbo. Nó là một preset/chế độ riêng, giúp giữ khả năng dùng repo cho các loại video khác và làm việc kiểm thử rõ ràng hơn.

## 11. Sửa lỗi liên quan

Trong phạm vi triển khai cần sửa hai vấn đề đang ảnh hưởng trực tiếp:

- Chuỗi tiếng Việt trong các file đã tùy biến đang hiển thị sai encoding.
- `config.save_config()` đang bị gọi trùng ở cuối `webui/Main.py`, kèm một lời gọi `_bottom()` không có định nghĩa trong file.

Không thực hiện refactor lớn ngoài các phần cần thiết cho chế độ bán xe.

## 12. Kiểm thử và tiêu chí hoàn thành

Kiểm thử tự động bao gồm:

- Validation dữ liệu xe bắt buộc và tùy chọn.
- Prompt chứa đúng dữ liệu xe và không biến trường trống thành khẳng định.
- Prompt yêu cầu hook 1-3 giây, độ dài 35-45 giây và CTA Minh Dũng.
- Chế độ công khai giá và ẩn giá tạo yêu cầu khác nhau.
- Bộ kiểm tra phát hiện khẳng định không được hỗ trợ như "zin đét" hoặc "ODO chuẩn".
- Metadata tạo đúng nền tảng và chứa thông tin liên hệ cần thiết.
- Giá trị mặc định WebUI dùng video dọc, nguồn local và nối tuần tự.

Kiểm thử thủ công bao gồm:

- Nhập một xe mẫu đầy đủ và tạo kịch bản.
- Xác nhận có thể sửa kịch bản trước khi dựng.
- Upload lẫn ảnh và video rồi xác nhận thứ tự được giữ nguyên.
- Tạo một video dọc hoàn chỉnh và kiểm tra giọng đọc, phụ đề, CTA.
- Kiểm tra WebUI tiếng Việt hiển thị đúng dấu.

Tính năng hoàn thành khi người dùng có thể nhập dữ liệu một chiếc xe, nhận kịch bản bán hàng đúng giọng thương hiệu, chỉnh sửa, dựng video 9:16 và lấy caption cho TikTok/Facebook mà không phải viết prompt thủ công.
