import numpy as np
# c
from robotPi import robotPi
import cv2
from rev_cam import rev_cam  # 摄像头倒转添加
import os
import time
from robotpi_movement import Movement

robot = robotPi()
forwardspeed = 42
forwardspeed2 = 84
# 北京工业大学终结者1队
# 20220610

'''
阈值时间
多次判断
飘移
霍夫圆判断
socket网络传输（骚）
信息熵
高斯滤波
卡尔曼滤波

'''
# 可调节参数：
threshold_yuzhi = 100  # 二值化阈值
raw_height = 480  # 原始视频高度
raw_width = 640  # 原始视频宽度
width = 64
height = 30
resized_height = 48


#hit target
width2 = 480
height2 = 180
fw_time = 1000  # 击靶前进时间
fw_speed = 20  # 击靶前进速度
ssumyuzhi = 2.1e+07  # 画面数组最大值
flag_max = 2  # 数组判断最大值
MinRadius = 2  # 最小霍夫圆圈
MaxRadius = 200  # 最大霍夫圆圈
minyuanxinyuzhi = 235  # 最小圆心阈值
maxyuanxinyuzhi = 285  # 最大圆心阈值
red_yuzhi = 5  # 红色二值化阈值
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (6, 6))



def process_input(num):
    if num == 1:
        robot.movement.move_free(speed= 0, direction = -55, w = -400,times=250)
        print("111111")
        return 0
    elif num == 2:
        robot.movement.move_free(speed= 0, direction = -25, w = -200,times=250)
        print("222222")
        return 0
    elif num == 3:
        robot.movement.move_free(speed= 0, direction = -15, w = 0,times=150)
        print("333333")
        return 0
    elif num == 4:
        robot.movement.move_free(speed= 0, direction = 15, w = 0,times=150)
        print("444444")
        return 0
    elif num == 5:
        robot.movement.move_free(speed= 0, direction = 45, w = 200,times=250)
        print("555555")
        return 0
    elif num == 6:
        robot.movement.move_free(speed= 0, direction = 55, w = 400,times=250)
        print("666666")
        return 0
    else:
        return "move_error"



def my_circle(grey ,img_x, img_y):
    mid_x = 0
    mid_y = 0
    area = 0
    for i in range (0, img_y-1):
        for j in range(0, img_x-1):
            if grey[i][j] == 255:
                area = area + 1
                mid_x = mid_x + j
                mid_y = mid_y + i
    if area == 0:
        return 0,0,0,0 
    mid_x = mid_x // area
    mid_y = mid_y // area
    mid_radius = round(pow(area/3.141,1/2))
    print(mid_x,mid_y,area,mid_radius)
    return mid_x,mid_y,area,mid_radius                   


def pidadjust(mid_x,area,wid):
    mid_x = mid_x-2
    E0 = wid/2 - mid_x
    min_yuan = wid/2-1
    max_yuan = wid/2+3
    p = E0
    if mid_x >= min_yuan and mid_x <= max_yuan:
        print("forward")
        if area >= 10:
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
        

def adjust():  # 击靶调整
    time_d = 0
    adjust_flag = 0#左右旋转参数
    cv2.destroyAllWindows()# 关闭所有窗口，即cap
    cap.release()
    cap1 = cv2.VideoCapture(0)# 调用击靶摄像头
    while True:
        if cap1.isOpened():
            time_hough_start = time.time()
            while True:
                times1 = time.time()
                ret, frame1 = cap1.read()
                frame1 = cv2.resize(frame1, (40, 30))
                cv2.waitKey(1)
                hsv = cv2.cvtColor(frame1, cv2.COLOR_BGR2HSV)  # HSV空间
                lower_red = np.array([0, 119, 132], np.uint8)  # 设定红色的阈值
                upper_red = np.array([67, 255, 255], np.uint8)
                mask = cv2.inRange(hsv, lower_red, upper_red)  # 设定取值范围
                res1 = cv2.bitwise_and(frame1, frame1, mask=mask)  # 对原图像处理
                grey = cv2.cvtColor(res1, cv2.COLOR_BGR2GRAY)
                grey = rev_cam(grey)
                grey = cv2.medianBlur(grey,5)               
                _, grey = cv2.threshold(grey, 5, 255, cv2.THRESH_BINARY)
                mid_x,mid_y,area,mid_radius = my_circle(grey ,40, 30)
                if area >= 1:
                    cv2.circle(grey, (mid_x, mid_y), 3, (100, 100, 100), 3)  # 画圆心
                    pidadjust(mid_x,area,40)
                else :
                    print("nocircle")
                    robot.movement.move_free(speed= 15, direction = 0, w = 0,times=300)
                times2 = time.time()
                times3 = times2 - times1
                print(times3)
                # cv2.imshow('res1',frame1)
        else:
            print("hough error")
            break
    time.sleep(1)

def find_end(grey,img_width,img_high):
    left_black = 0
    right_black = 0
    for i in range(0,img_high-1):
        for j in range(0,img_width//2-1):
            if grey[i][j] == 0:
                left_black = left_black+1
        for j in range(img_width//2,img_width-1):
            if grey[i][j] == 0:
                right_black = right_black+1
    print(left_black,right_black)
    return left_black,right_black 

def judge(res):
    value = 0
    x1 = 0
    y1 = 0  # 左上角
    x2 = 0
    y2 = 0  # 右上角
    n=0
    sum = 0
    b = 0
    c = 0
    for i in range(0,9):
        for j in range(0,9-i):
          if res[[j],[63-i]]<=80:
              x2 = x2 + 1
          else:
              break
    if x2>=30:
       
        return 1
    for i in range(0,9):
        for j in range(0,9-i):
          if res[[j],[i]]<=80:
              x1 = x1 + 1
          else:
              break
    if x1>=30:
        return 2
    return value

def move(value):
    if value == 0:
        robot.movement.move_free(speed=70, direction = 0, w = 0,times=300)
        print('forward1')
    elif value == 1:
        robot.movement.move_free(speed=100, direction = 0, w = 330 , times=300)
        print('left1')
    elif value == 2:
        robot.movement.move_free(speed=100, direction = -0, w = -330,times=300)
        print('right1')
    pass

def move2(value):
    if value == 0:
        robot.movement.move_free(speed=70, direction = 0, w = 0,times=300)
        print('forward2')
    elif value == 1:
        robot.movement.move_free(speed=100, direction = 10, w = 100 , times=100)
        print('left2')
    elif value == 2:
        robot.movement.move_free(speed=100, direction = -10, w = -100,times=300)
        print('right2')
    pass

def move3(value):
    if value == 0:
        robot.movement.move_free(speed=20, direction = 0, w = 0,times=300)
        print('forward3')
    elif value == 1:
        robot.movement.move_free(speed=20, direction = 10, w = 100 , times=100)
        print('left3')
    elif value == 2:
        robot.movement.move_free(speed=20, direction = -10, w = -100,times=300)
        print('right3')
    pass


if __name__ == '__main__':

    cap = cv2.VideoCapture(1)
    cap.set(3,width)
    cap.set(4,resized_height)
    robot.movement.wave_hands()
    #input("########wait for begin#########")
    num = int(input("size========="))
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
        cv2.imshow('res',res)
        cv2.waitKey(1)
        res[:, 0] = res[:, 1]
        value = judge(res)
        if timec <= 7:
            move(value)
        if timec > 7 and timec <= 8.75:
            move(value)
        if timec > 8.75:
            move3(value)
            lefts,rights = find_end(res,width,resized_height - height)
            if lefts >= 40 and rights >= 40:
                break
        if timec > 60:
                break
        time2 = time.time()
        time3 = time2 - time1
        
        print(time3)
    #robot.movement.move_free(speed=0, direction = 0, w = 0,times=100)
    adjust()
