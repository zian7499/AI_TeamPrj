import socket
import threading
import time
# import codecs
import cv2

# import base64


# 서버 정보
host = '10.10.21.110'
port = 30000

# 서버 socket 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen()

# client 소켓 정보를 담을 리스트
client_socket_list = []

# 변수 초기화(받아야 할 파일 크기)
# 테스트에 사용된 이미지 번호
file_name = ''
file_size = 0
user_ip = ''


# 데이터를 수신하는 함수
def read_data():
    file_path = "C:\\Users\\lms110\\Desktop\\Python\\image1.jpg"

    detected_shapes = detect_shapes(file_path)

    shape_area = {}

    if not detected_shapes:
        print("검출된 도형이 없습니다.")

    for shape, contour, _ in detected_shapes:

        if shape != "알 수 없음":
            area = cv2.contourArea(contour)
            shape_area[shape] = shape_area.get(shape, 0) + area


        if not shape_area:
            print("검출된 도형이 없습니다.")

        else:
            max_area_shape = max(shape_area, key=shape_area.get)


            for shape, contour, _ in detected_shapes:
                if shape == max_area_shape:
                    angle = get_angle_of_shape(contour, shape)
                    print(angle)
                    break


            value = round(get_pleasure_value(max_area_shape, angle), 2)
            print(f"가장 넓은 면적을 차지하는 도형: {max_area_shape}, 각도: {angle}, 감정 값: {value}")
            return value


def send_msg():
    while True:
        # 입력된 텍스트를 변수에 담기
        send_message = input()
        # 소켓 리스트에 존재하는 모든 소켓에 데이터 전송
        for client in client_socket_list:
            client.send(send_message.encode('utf-8'))


def detect_shapes(img_path):
    # file_path에서 이미지 읽기
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    # 이미지를 회색조로 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 회색조 이미지에 (윤곽선을 따는)가우시안 블러 적용
    # (5, 5) : 커널 크기, 0 : 표준 편차
    bluured = cv2.GaussianBlur(gray, (5, 5), 0)
    # 가우시안 블러가 적용된 이미지에서 엣지 검출(Canny Edge)
    # 100 이상 200 미만을 임계값으로 Edge 인식
    edges = cv2.Canny(bluured, 100, 200)
    # Edge에서 윤곽선 찾기
    # findContours : 윤곽선 정보, 윤곽선 계층 정보, 원본 이미지 반환으로 , _를 사용하여 쓰지 않음
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # 도형 데이터를 저장할 리스트
    shape_data = []

    # 윤곽선 순회
    for contour in contours:
        # 윤곽선의 면적을 계산
        area = cv2.contourArea(contour)
        # 면적이 500보다 작은 윤곽선은 무시
        if area < 500:
            continue

        # 윤곽선의 근사화 정도 설정
        epsilon = 0.045 * cv2.arcLength(contour, True)
        # contour을 epsilon 값에 따라 근사화한 도형 반환, True는 닫혀있는 도형
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # 근사화한 윤곽선의 꼭지점 수에 따라 도형의 종류 결정
        if len(approx) == 3:
            shape_name = "삼각형"
        elif len(approx) == 4:
            shape_name = "사각형"
        elif len(approx) >= 5:
            shape_name = "원"
        else:
            shape_name = "알 수 없음"

        print(len(approx))
        # 윤곽선의 중심점을 계산
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0

        # 도형의 이름 윤곽선, 중심점을 리스트에 추가
        shape_data.append((shape_name, contour, (cX, cY)))
        print(shape_name)
    # 도형 데이터를 반환
    return shape_data


# 도형의 각도를 계산하는 함수
def get_angle_of_shape(angle_contour, angle_shape_name):
    # 원이면 각도는 0
    if angle_shape_name == "원":
        return 0.0

    # 윤곽선을 사용하여 타원을 근사화하고 그 각도를 계산
    (x, y), (MA, ma), angle = cv2.fitEllipse(angle_contour)
    return angle


def get_pleasure_value(senti_shape, senti_angle):
    shape_value = {
        "삼각형": -1.0,
        "사각형": -0.5,
        "원": 0.7
    }

    angle_value = [
        (0, 0, 0.7),
        (1, 15, 0.6),
        (16, 30, 0.3),
        (31, 45, 0.1),
        (46, 60, -0.1),
        (61, 75, -0.1),
        (76, 90, -0.1),
        (91, 105, 0.4),
        (106, 120, -0.1),
        (121, 135, -0.3),
        (136, 150, -0.5),
        (151, 165, -0.1),
        (166, 179, -0.1),
        (180, 180, 0.4)
    ]

    shape_val = shape_value.get(senti_shape, 0)
    angle_val = 0

    if senti_shape != "원":
        for start, end, val in angle_value:
            if start <= senti_angle <= end:
                angle_val = val
                break

    value = shape_val + angle_val
    return min(max(value, -1.0), 1.0)


while True:

    image_value = read_data()
    print(image_value)
    # accept : 클라이언트 소켓, 클라이언트 주소 정보 반환
    client_socket, client_address = server_socket.accept()
    # 생성된 소켓 리스트에 append
    client_socket_list.append(client_socket)

    print(f"클라이언트가 {client_address}에서 연결되었습니다.")

    # args = client_socket, << 단일 항목인 경우에도 ,을 붙여야 함.(문법)
    client_accept = threading.Thread(target=read_data, args=(client_socket,))
    to_client_msg = threading.Thread(target=send_msg)

    client_accept.start()
    to_client_msg.start()
