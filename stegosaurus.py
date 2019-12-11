from png_steg import encrypt,decrypt,DataExcessError,TooBigError,FilenameLengthError,BitDepthError

def pngenc(im,dat,p,b=1,fn=''):
    try:
        encrypt(im,dat,p,b,fn)
    except DataExcessError as e:
        bd = e.neededbits
        print('The target image has insufficient pixels to store the target data in the least significant bit.')
        if bd>8:
            print('The data is too large to fit with any size bit overwrite.')
        else:
            effects=['','','be essentially unnoticable.','be a little noticable.',
                     'be somewhat noticable.','be very noticable.','mostly obliterate the image.','obliterate the image.','completely, mercilessly, irrevocably incinerate the image']
            print('The data needs to overwrite the {} least significant bits'.format(bd))
            print('This will '+effects[bd])
            i = input("Type [{}] to proceed, anything else to stop.".format(bd))
            if i==str(bd):
                pngenc(im,dat,p,bd,fn)
            return
    except TooBigError:
        print("The maximum amount of data that I can store in on image is 16777215 bytes, about 16 Megabytes.")
    except FilenameLengthError:
        if '.' in dat:
            bs = '.'.join(dat.split('.')[:-1])
            fs = dat.split('.')[-1]
            if len(fs)>8:
                newname=dat[:255]
            else:
                newname=bs[:254-len(fs)]+'.'+fs
        else:
            newname=dat[:255]
        print("The maximum filename length I can process is 255 bytes.")
        print("I can rename the file to: \n"+newname)
        i = input("Type [y] to proceed")
        if i=='y' or i=='Y':
            pngenc(im,dat,p,bd,newname)
        return
    except BitDepthError:
        print('Error while decrypting. Double check password.')
pngenc('image.png','data.file','password')
decrypt('image.png','password')
