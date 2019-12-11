from PIL import Image as I
from  os.path import getsize
import hashlib
def sha1_(s):
    return hashlib.sha1(s).digest()#160 bit
def sha1(s):
    return hashlib.sha1(s.encode()).digest()#160 bit

class ModeError(Exception):#only RGB,RGBA, and CMYK pngs supported
    pass
class DataExcessError(Exception):
    def __init__(self, arg):
        self.neededbits = arg
    pass
class TooBigError(Exception):
    pass
class FilenameLengthError(Exception):
    pass
class BitDepthError(Exception):
    pass
def bytetostr(b):
    r=''
    for i in b:r+=chr(i)
    return r
def bit(b,i,bd):
    return (b//(2**(bd-i-1)))%2
def bit_s(b,i):
    return (b//(2**(7-i)))%2
def decrypt_(li,s,e,k,h,w,bd):
    b=b''
    for i in range(s,e,8):
        n=0
        for j in range(i,i+8):
            n*=2
            n+=bit(li[((j//bd)//3)%w,((j//bd)//3)//w][(j//bd)%3],j%bd,bd)
        b+=bytes([n])
    return bytes(b[i]^k[i] for i in range(len(b)))

def crypt(li,s,e,k,d,h,w,bd):
    rt = bytes(d[i]^k[i] for i in range(len(d)))
    for i in range(s,e,8):
        n=rt[(i-s)//8]
        for j in range(i,i+8):
            lt = list(li[((j//bd)//3)%w,((j//bd)//3)//w])
            lt[(j//bd)%3]=(2**(bd-j%bd))*(lt[(j//bd)%3]//(2**(bd-j%bd))) + bit_s(n,j-i)*(2**(bd-j%bd-1))+(lt[(j//bd)%3]%(2**(bd-j%bd-1)))
            li[((j//bd)//3)%w,((j//bd)//3)//w] = tuple(lt)
    
def encrypt(im_file,dat_file,password,maxbitoverride=1,fnameoverride=''):
    bd=maxbitoverride#bit depth
    if fnameoverride=='':fnameoverride=dat_file
    if len(fnameoverride)>=256:raise FilenameLengthError
    im=I.open(im_file)
    if im.mode in ("RGB","RGBA","CMYK"):
        pixbytes=3
    else:
        raise ModeError
    w,h=im.width,im.height
    imbytes = pixbytes*w*h
    databytes = getsize(dat_file)
    if databytes>=2**24:
        raise TooBigError
    neededbitoverride=(bd+8*(databytes+4+len(fnameoverride))-1)//imbytes+1#how many bits in each rgb channel to overwrite
    if neededbitoverride>maxbitoverride:
        raise DataExcessError(neededbitoverride)
    il=im.load()
    il[0,0]=(bd,il[0,0][1],il[0,0][2])#major security issues right here
    ###  metadata time:filename size, 1 byte; bitoverwrite, 1 byte; data size, 3 bytes; filename, 0-255 bytes
    metadata=bytes([len(fnameoverride)])+bytes((databytes//(65536),(databytes//256)%256,databytes%256))+bytes(fnameoverride,'UTF-8')
    for ii in range(0,len(metadata)*8,160):
        key=sha1(password+str(ii//160))
        crypt(il,bd+ii,bd+min(ii+160,len(metadata)*8),key,metadata[ii//8:min(ii+160,len(metadata)*8)//8],h,w,bd)
    i=len(metadata)*8
    ms=i+databytes*8
    with open(dat_file,'rb') as f:
        bb = f.read(20)
        key=sha1(password)
        while bb!=b'':
            crypt(il,bd+i,bd+min(i+160,ms),key,bb,h,w,bd)
            key=sha1_(key)
            bb=f.read(20)
            i+=160
    im.save(im_file)
def decrypt(im_file,password):
    im=I.open(im_file)
    if im.mode in ("RGB","RGBA","CMYK"):
        pixbytes=3
    else:
        raise ModeError
    w,h=im.width,im.height
    imbytes = pixbytes*w*h
    il=im.load()
    bd = il[0,0][0]
    if bd>8:raise BitDepthError
    key=sha1(password+'0')
    m=decrypt_(il,bd,32+bd,key[:4],h,w,bd)
    fnamelength=m[0]
    fname=b''
    for i in range(0,(fnamelength+4),20):
        key=sha1(password+str(i//20))
        fname+=decrypt_(il,bd+i*8,bd+min((i+20)*8,fnamelength*8+32),key,w,h,bd)
    databytes=fname[1]*65536+fname[2]*256+fname[3]
    fname=fname[4:]
    ms=32+len(fname)*8+databytes*8
    i=32+len(fname)*8
    with open(bytetostr(fname),'wb+') as f:
        key=sha1(password)
        while i<ms:
            dd=decrypt_(il,bd+i,bd+min(i+160,ms),key,h,w,bd)
            key=sha1_(key)
            f.write(dd)
            i+=160
