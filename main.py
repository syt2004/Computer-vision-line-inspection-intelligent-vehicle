import numpy as np
from robotPi import robotPi
import cv2
from rev_cam import rev_cam  
import time
from robotpi_movement import Movement
import math

robot = robotPi()

# 可调节参数：
threshold_yuzhi = 100  # 二值化阈值
raw_height = 480  # 原始视频高度
raw_width = 640  # 原始视频宽度
width = 64
height = 30
resized_height = 48

def process_input(num):#根据裁判放的不同的角度手动调整机器人运动
    movements = {
        1: {'speed': 0, 'direction': -55, 'w': -400, 'times': 250},
        2: {'speed': 0, 'direction': -25, 'w': -200, 'times': 250},
        3: {'speed': 0, 'direction': -15, 'w': 0, 'times': 150},
        4: {'speed': 0, 'direction': 15, 'w': 0, 'times': 150},
        5: {'speed': 0, 'direction': 45, 'w': 200, 'times': 250},
        6: {'speed': 0, 'direction': 55, 'w': 400, 'times': 250}
    }
    move = movements.get(num)
    if move:
        robot.movement.move_free(**move)
         print(f"Input {num} processed.")
        return 0
    return "move_error"

def my_circle(grey,img_x, img_y):#根据灰度图计算圆心位置
    grey = np.asarray(grey)#将灰度图传入一个矩阵中
    if grey.shape[0] != img_y or grey.shape[1] != img_x:
        raise ValueError("Image dimensions do not match the provided width and height.")
    white_pixels = (grey == 255)
    y_coords, x_coords = np.where(white_pixels)
    if y_coords.size == 0:
        return 0, 0, 0, 0#找不到合适的元素点
    
    mid_y = np.mean(y_coords)
    mid_x = np.mean(x_coords)#计算灰度图为255的各个点位置的加权中心
    area = y_coords.size
    mid_radius = round(np.sqrt(area / np.pi))
    
    return mid_x, mid_y, area, mid_radius

def white_center(grey, resized_height, resized_width):#寻找白色道路的加权中心
    grey = np.asarray(grey)
    if grey.shape != (resized_height, resized_width):
        raise ValueError("Image dimensions do not match the provided width and height.")
    
    white_pixels = (grey == 255)
    y_coords, x_coords = np.where(white_pixels)
    if y_coords.size == 0:
        return 0, 0  
    mid_y = np.mean(y_coords)
    mid_x = np.mean(x_coords)
    
    return mid_y, mid_x

def slope(x1, y1, x2, y2):
    if x2 - x1 == 0:
        return float('inf')
    else:
        return (y1 - y2) / (x2 - x1)#摄像头捕获图片y轴方向与现实中的相反

def process_image(res, raw_width, raw_height):#处理图像过程
    if res.shape != (raw_height, raw_width):
        raise ValueError("Image dimensions do not match the provided width and height2.")#确保输入图像是numpy数组
    area_1 = res[199:370, :]#可调参数，如果分辨率变化，要调这一部分参数
    area_2 = res[99:200, :]
    height_1 = 171#随着前两个的改变，也要改变
    height_2 = 101#有可能有计算错误

    area_1_mid_y, area_1_mid_x = white_center(area_1, height_1, raw_width)#调用函数，求出两块白色区域的中心
    area_2_mid_y, area_2_mid_x = white_center(area_2, height_2, raw_width)
    slope(area_2_mid_x, area_2_mid_y, area_1_mid_x, area_1_mid_y)#计算两点构成直线的斜率
    #计算角度
    return slope

def Wwww(slope):#角速度的计算，有待商榷 def Wwww(slope）：

    omega = 250/slope
    return omega

def pidadjust(mid_x,area,wid):#根据圆心位置和面积调整机器人运动
    mid_x = mid_x-2
    E0 = wid/2 - mid_x
    min_yuan = wid/2-1
    max_yuan = wid/2+3
    p = E0
    if mid_x >= min_yuan and mid_x <= max_yuan:
        print("forward")
        if area >= 40:
            robot.movement.hit()
            print("hit")
            time.sleep(100000)
        else:
            if 34-area<10:
                robot.movement.move_free(speed=10, direction = 0, w = 0,times=300)
            else:
                robot.movement.move_free(speed= 33-area, direction = 0, w = 0,times=300)
    elif mid_x >= max_yuan:
        print("turn right")
        robot.movement.move_free(speed= int(-p), direction = 270, w = -20,times=150)
    else:
        print("turn left")
        robot.movement.move_free(speed= int(p) + 3, direction = 90, w = 20,times=150)
        

def adjust():  # 击靶调整# time_d = 0 adjust_flag = 0#左右旋转参数
    cv2.destroyAllWindows()# 关闭所有窗口，即cap
    cap.release()
    cap1 = cv2.VideoCapture(0)# 调用击靶摄像头
    while True:
        if cap1.isOpened():
            while True:
                times1 = time.time()
                ret, frame = cap1.read()
                frame = cv2.resize(frame, (40, 30))
                cv2.waitKey(1)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)# 将图像从 BGR 转换为 HSV

                lower_red1 = np.array([0, 100, 100])#定义红色的HSV范围
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([160, 100, 100])
                upper_red2 = np.array([180, 255, 255])

                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask = mask1 | mask2#创建眼膜提取红色区域
                mask = rev_cam(mask)
                mask = cv2.medianBlur(mask,5)   
                mid_x,mid_y,area,mid_radius = my_circle(mask ,40, 30)

                if area >= 1:
                    cv2.circle(mask, (int(mid_x),int(mid_y)), 3, (100, 100, 100), 3)  # 画圆心
                    pidadjust(mid_x,area,40)
                else :
                    print("nocircle")
                    robot.movement.move_free(speed= 15, direction = 0, w = 0,times=300)
                times2 = time.time()
                times3 = times2 - times1
                print(times3)
        else:
            print("hough error")
            break

    time.sleep(1)

def find_end(grey, img_width, img_height):##停车的函数
    grey = np.asarray(grey)
    if grey.shape[0] != img_height or grey.shape[1] != img_width:
        raise ValueError("Image dimensions do not match the provided width and height.")
    mid_point = img_width // 2#找到中轴
    left_black = np.sum(grey[:, :mid_point] == 0)#用布尔索引计算左右两边黑色像素点的个数
    right_black = np.sum(grey[:, mid_point:] == 0)
    
    return left_black, right_black

def move(omega):
        robot.movement.move_free(speed=65, direction = 0, w = omega,times=300)#此处将之前的左右转常量w变为一个变量omega，根据斜率的变化时刻改变的w，负为右，正为左所以不用返回值来表示左或右
        print('我是东哥')

if __name__ == '__main__':

    cap = cv2.VideoCapture(1)
    cap.set(3,width)
    cap.set(4,resized_height)
    robot.movement.wave_hands()

    num = int(input("Input(0-6):==>  "))
    process_input(num)
    
    time1 = time0 = time.time()
    while cap.isOpened():
        ret, frame = cap.read()
        time1 = time.time()
        timec = time1 - time0
        frame = cv2.resize(frame, (width, resized_height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _,frame = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY)
        res = frame[resized_height - height:, :]
        # cv2.imshow('res',ret)
        cv2.waitKey(1)#打开摄像头后的处理图像部分

        res[:, 0] = res[:, 1]
        omega =Wwww(angle_degrees, kp=1.0, omega_min=-330, omega_max=330)

        if timec <= 8:#因为本程序是拿时间来卡运动的，所以此处时间不合适可以修改
            move(omega)
            res2 = frame[:resized_height - height, :]
            lefts,rights = find_end(res2,width,resized_height - height)
            if lefts >= 80 and rights >= 80:
                break
        if timec > 60:
                break
        time2 = time.time()
        time3 = time2 - time1
        print(time3)
    adjust()