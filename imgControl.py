import numpy as np
import matplotlib.pyplot as plt

def Layer(img, capa): #0-Rojo, 1-Verde, 2-Azul
    img_capa = np.zeros_like(img)
    img_capa[:,:,capa] = img[:,:,capa]
    return img_capa

def Canal(img, canal): #0-Rojo, 1-Verde, 2-Azul
    imgN = np.copy(img)
    if canal == 0:
        imgN[:,:,1] = 1
        imgN[:,:,2] = 1
    elif canal == 1:
        imgN[:,:,0] = 1
        imgN[:,:,2] = 1
    elif canal == 2:
        imgN[:,:,0] = 1
        imgN[:,:,1] = 1
    return imgN

def Negativo(img):
    imgN = np.copy(img)
    imgN = 1 - imgN
    return imgN

def CombinarF(img1, img2, factor):
    imgN1 = np.copy(img1)
    imgN2 = np.copy(img2)
    imgN = factor * imgN1 + (1 - factor) * imgN2
    return imgN

def Grises(img):
    imgN = np.copy(img)
    imgN = imgN[:,:,0] * 0.299 + imgN[:,:,1] * 0.587 + imgN[:,:,2] * 0.114
    return imgN

def SumarBrillo(img, brillo):
    imgN = np.copy(img)
    imgN = imgN + brillo
    return imgN

def AjusteCanal(img, canal, ajuste):
    imgN = np.copy(img)
    imgN[:,:,canal] = imgN[:,:,canal] + ajuste
    return imgN

def AjusteContraste(img, zonas, contraste):
    imgN = np.copy(img)
    if zonas == 0:
        imgN = contraste * np.log10(1 + imgN)
    elif zonas == 1:
        imgN = contraste * np.exp(imgN - 1)
    return imgN

def Binaria(img, umbral):
    imgN = np.copy(img)
    Gris = Grises(imgN)
    imgN = (Gris > umbral)
    return imgN

def Desplazar(img, dx, dy):
    imgN = np.copy(img)
    h, w = imgN.shape[:2]
    xI = 0
    xF = w - dx
    yI = 0
    yF = h - dy
    trasladada = np.zeros_like(imgN)
    trasladada[dy:h, dx:w] = imgN[yI:yF, xI:xF]
    return trasladada

def Recortar(img, xI, xF, yI, yF):
    imgN = np.copy(img)
    recortada = imgN[xI:xF, yI:yF]
    return recortada

#Rotar
def RotarImg(img, angulo):
    imgN = np.copy(img)
    h, w = imgN.shape[:2]
    centro = (w // 2, h // 2)
    theta = np.deg2rad(angulo)
    rotated = np.zeros_like(imgN)
    for y in range(h):
        for x in range(w):
            x0 = x - centro[0]
            y0 = y - centro[1]
            xr = int(np.round(x0 * np.cos(theta) - y0 * np.sin(theta) + centro[0]))
            yr = int(np.round(x0 * np.sin(theta) + y0 * np.cos(theta) + centro[1]))
            if 0 <= xr < w and 0 <= yr < h:
                rotated[y, x] = imgN[yr, xr]
    return rotated
    
#Reducir Resolucion
def ReducirResolucion(img, factor):
    imgN = np.copy(img)
    h, w = imgN.shape[:2]
    h_new = h // factor
    w_new = w // factor
    reduced = np.zeros((h_new, w_new, imgN.shape[2]), dtype=imgN.dtype)
    for i in range(h_new):
        for j in range(w_new):
            reduced[i, j] = imgN[i*factor:(i+1)*factor, j*factor:(j+1)*factor].mean(axis=(0, 1))
    return reduced

#Ampliar
def Ampliar(img, factor):
    imgN = np.copy(img)
    h, w = imgN.shape[:2]
    h_new = h * factor
    w_new = w * factor
    enlarged = np.zeros((h_new, w_new, imgN.shape[2]), dtype=imgN.dtype)
    for i in range(h):
        for j in range(w):
            enlarged[i*factor:(i+1)*factor, j*factor:(j+1)*factor] = imgN[i, j]
    return enlarged

#Histograma
def Histograma(img):
    imgN = np.copy(img)
    h, w = imgN.shape[:2]
    histR = np.zeros(256)
    histG = np.zeros(256)
    histB = np.zeros(256)
    for i in range(h):
        for j in range(w):
            r = int(imgN[i, j, 0] * 255)
            g = int(imgN[i, j, 1] * 255)
            b = int(imgN[i, j, 2] * 255)
            histR[r] += 1
            histG[g] += 1
            histB[b] += 1
    return histR, histG, histB
