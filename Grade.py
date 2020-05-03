import cv2 as cv
import numpy as np 
import csv
import os
import tkinter as tk

path = ''

root = tk.Tk()

canvas1 = tk.Canvas(root, width=400, height=300)
canvas1.pack()

entry1 = tk.Entry(root)
canvas1.create_window(200, 140, window=entry1)
label1 = tk.Label(root, text='please enter the path to the folder "Answers"')
canvas1.create_window(200, 230, window=label1)


def getpath():
    global path
    path = entry1.get()


button1 = tk.Button(text='Enter Path', command=getpath)
canvas1.create_window(200, 180, window=button1)

root.mainloop()

var1 = os.listdir(path)
names = []
sheets = []
results = []
rows = []
for entry in var1:
    if ('.jpg' or '.png' or '.jpeg') in entry:
        epath = path + '\\' + entry
        tmp_im = cv.imread(epath, 0)
        sheets.append(tmp_im)
        names.append(entry[0:-4])

mask = cv.imread('mask.jpg', 0)  # load the mask of model answer generated by draw.py
org = cv.imread('Test.jpg', 0)  # load the test without answers
org = cv.resize(org, (460, 654))

for sheet in sheets:

    image = cv.resize(sheet, (460, 654))

    answers = cv.bitwise_xor(org, image)

    ans_bw = cv.inRange(answers, 90, 255)
    ans_bw_cp = ans_bw.copy()
    msk = cv.resize(ans_bw, (462, 656))
    cv.floodFill(ans_bw, msk, (0, 0), 255)

    ans_inv = cv.bitwise_not(ans_bw)
    # ans_img = cv.bitwise_xor(ans_inv, ans_bw_cp)
    ans_img_not_filtered = cv.bitwise_xor(ans_inv, ans_bw_cp)

    # ans_img_8bit=image.astype(np.uint8)#8bit convertion (uint8,uint16)

    # ans_img =small_reg(ans_img_8bit,50)
    ans_img = cv.medianBlur(ans_img_not_filtered, 9)

    #cv.imwrite('ans_mask.jpg', ans_img)

    _, threshold = cv.threshold(mask, 110, 255, cv.THRESH_BINARY)

    # Detecting contours in image.
    contours, _ = cv.findContours(threshold, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # generating photo for every question
    center_contour_list = []
    for c in contours:
        # compute the center of the contour
        M = cv.moments(c)
        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])
        center_contour_point = (x, y)
        center_contour_list.append(center_contour_point)  # save center of contours

    # for loop to save the cropped photos in list
    num = 0
    height = mask.shape[0]
    width = mask.shape[1]

    croped_list = []
    for num in range(len(contours)):

        if num == 0:
            saved_croped = mask[int(((center_contour_list[num][1])+(center_contour_list[num+1][1]))/2): height, 0:width]
        elif num == (len(contours)-1):
            saved_croped = mask[0: int(((center_contour_list[num-1][1])+(center_contour_list[num][1]))/2), 0:width]
        else:
            saved_croped = mask[int(((center_contour_list[num][1])+(center_contour_list[num+1][1]))/2):int(((center_contour_list[num-1][1])+(center_contour_list[num][1]))/2) , 0:width]

        croped_list.append(saved_croped)  # save the cropped photos in list

    # generating  photo for every answer
    croped_list_ans = []
    for num in range(len(contours)):

        if num == 0:
            saved_croped_ans = ans_img[int(((center_contour_list[num][1])+(center_contour_list[num+1][1]))/2): height, 0:width]
        elif num == (len(contours)-1):
            saved_croped_ans = ans_img[0: int(((center_contour_list[num-1][1])+(center_contour_list[num][1]))/2), 0:width]
        else:
            saved_croped_ans = ans_img[int(((center_contour_list[num][1])+(center_contour_list[num+1][1]))/2):int(((center_contour_list[num-1][1])+(center_contour_list[num][1]))/2), 0:width]

        croped_list_ans.append(saved_croped_ans)
        # save the cropped photos in list

    # generating xor photo for every question
    xored_croped_list = []
    for num in range(len(contours)):

        xored_img = cv.bitwise_xor(croped_list_ans[num], croped_list[num], mask=None)
        xored_croped_list.append(xored_img)

    correction_list = []
    for num in range(len(contours)):
        contoures_cropped_ans, _ = cv.findContours(croped_list_ans[num], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        pixel_num_before = cv.countNonZero(croped_list[num])
        pixel_num_after = cv.countNonZero(xored_croped_list[num])
        if len(contoures_cropped_ans) > 1:
            correction_list.append(0)
        else:
            if pixel_num_before > pixel_num_after:
                correction_list.append(1)
            elif pixel_num_before <= pixel_num_after:
                correction_list.append(0)

    results.append(correction_list.count(1).__str__()+'\\'+len(correction_list).__str__())


for name in names:
    tmp_lst = []
    tmp_lst.append(name)
    tmp_lst.append(results[names.index(name)])
    rows.append(tmp_lst)

f = open('Results.csv', 'w')

with f:
    writer = csv.writer(f)

    for row in rows:
        writer.writerow(row)