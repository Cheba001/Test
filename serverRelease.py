from http.server import HTTPServer, SimpleHTTPRequestHandler
import cgi
import os 
import html
import time
from datetime import datetime, date
from threading import Thread
import threading
import random
import picamera

server_address = ("", 8000)
       
class WorkThread(Thread):   
    def __init__(self):
        threading.Thread.__init__(self)
        self.eventPreview  = threading.Event()
        self.eventPhoto    = threading.Event()
        self.eventVideo    = threading.Event()
        self.eventSettings = threading.Event()
        self.eventWakeUp   = threading.Event()
        self.terminate = False
        self.camera         = 0
        self.videoLen       = 0
        self.recordTimeLost = 0
        self.lastPhoto      = ""
        
    def makePhoto(self,prev,video):
        filename = "preview.jpg";
        if prev == False:
            filename = "photo/" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S.jpg")
        
        if video == True:
            self.camera.capture(filename,use_video_port=True)
        else:
            self.camera.capture(filename)   
        self.lastPhoto = filename
        
    def run(self):
        while self.terminate != True:       
            self.eventWakeUp.wait()
            if self.camera == 0:
                self.camera = picamera.PiCamera()
            if self.eventVideo.is_set():
                self.eventVideo.clear()
                filename = "video/" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S.h264")
                self.recordTimeLost = self.videoLen
                camera.start_recording(filename)
                while self.recordTimeLost > 0:
                    camera.wait_recording(1)
                    if self.eventPreview.is_set():
                        self.makePhoto(True,True)
                    if self.eventPhoto.is_set():
                        self.eventPhoto.clear()
                        self.makePhoto(False,True)
                    self.recordTimeLost = self.recordTimeLost - 1
                camera.stop_recording()
                
            elif self.eventPreview.is_set():
                self.makePhoto(True,False)
                time.sleep(0.3)
            elif self.eventPhoto.is_set():
                self.eventPhoto.clear()
                self.makePhoto(False,False)
            else :
                self.eventWakeUp.clear()
                waitTime = 20
                needOff = True
                while waitTime > 0:
                    if self.eventWakeUp.is_set():
                       waitTime = 0
                       needOff = False
                    else:
                        waitTime = waitTime - 0.2
                        time.sleep(0.2)
                if needOff:
                    self.camera.close()
                    self.camera = 0
            
class CameraControl():
    def __init__(self): 
        self.workThread = WorkThread()      
        self.workThread.eventWakeUp.clear()
        self.workThread.start()

    def isOn(self):
        res = False
        if self.workThread.camera != 0:
            res = True
        return res
    def isPrev(self):
        return self.workThread.eventPreview.is_set()
    def isRec(self):
        return self.workThread.eventVideo.is_set()
      
    def zoom(self,x,y,w,h):
        if self.isOn():
            self.workThread.camera.zoom = (x,y,w,h)
        else:
            print("camera off!")
    def startPreview(self):
        self.workThread.eventWakeUp.set()
        self.workThread.eventPreview.set()
    def stopPreview(self):
        self.workThread.eventPreview.clear()
    def photo(self):
        self.workThread.eventWakeUp.set()
        self.workThread.eventPhoto.set()
    def video(self,len):
        self.workThread.videoLen = int(len)
        self.workThread.eventWakeUp.set()
        self.workThread.eventVideo.set() 
    def setResolution(self,w,h):
        if self.isOn():
            if not self.isRec():
                self.workThread.camera.resolution = (int(w),int(h))
    def set(self,vflip,hflip,brightness,exposure_compensation,saturation,sharpness):
        if self.isOn():
            if self.workThread.camera.vflip != bool(vflip):
                self.workThread.camera.vflip = bool(vflip)
            if self.workThread.camera.hflip != bool(hflip):
                self.workThread.camera.hflip = bool(hflip)
            if self.workThread.camera.brightness != int(brightness):
                self.workThread.camera.brightness = int(brightness)
            if self.workThread.camera.exposure_compensation != int(exposure_compensation):
                self.workThread.camera.exposure_compensation = int(exposure_compensation)
            if self.workThread.camera.saturation != int(saturation):
                self.workThread.camera.saturation = int(saturation)
            if self.workThread.camera.sharpness != int(sharpness):
                self.workThread.camera.sharpness = int(sharpness)
     
    def status(self,handler):
        val = b'{"statusOn":'
        print(int(self.isOn()))
        val += bytes(str(int(self.isOn())), 'utf-8')
        val += b',"statusPreviewOn":'
        val += bytes(str(int(self.isPrev())), 'utf-8')
        val += b',"statusVideoOn":'
        val += bytes(str(int(self.isRec())), 'utf-8')
        val += b',"statusRecLost":'
        val += bytes(str(self.workThread.recordTimeLost), 'utf-8')
        val += b',"lastPhoto":"'
        val += bytes(self.workThread.lastPhoto, 'utf-8')
        val += b'"}'
        handler.wfile.write(val)  

cameraCtl = CameraControl()




def video(len):
    videoThread = VideoThread(len)
    videoThread.start()
    
#_________RESULTS__________________
def getResPhoto(handler):
    files = os.listdir("photo") 
    images = filter(lambda x: x.endswith('.jpg'), files) 
    for it in images:
        name = str.encode(it)
        val = b"<span><img width='320' height='240' src='photo/"
        val += name
        val += b"'/><button id='photo/"
        val += name 
        val += b"' onclick='del(this)'>Del</button></span>"
        handler.wfile.write(val)

def getResVideo(handler):
    files = os.listdir("video") 
    vids = filter(lambda x: x.endswith('.mp4'), files) 
    for it in vids:
        name = str.encode(it)
        val = b"<span><button id='video/"
        val += name 
        val += b"' onclick='show(this)'>"
        val += name
        val += b"</button><button id='video/"
        val += name 
        val += b"' onclick='del(this)'>Del</button></span><br>"
        handler.wfile.write(val)      
        
def delete(f):
    print(f)
    os.remove(f)

def takeVideo(self):
    SimpleHTTPRequestHandler.do_GET(self)
    
#_______________HANDLER___________________________
class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        form = cgi.FieldStorage(
			fp=self.rfile,
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
				'CONTENT_TYPE':self.headers['Content-Type']
			})
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        
        action = html.escape(form.getfirst("action", ""))
        #-----camera-------
        if action == "start":
            cameraCtl.startPreview()
        elif action == "stop":
            cameraCtl.stopPreview()
        elif action == "photo":
            cameraCtl.photo()
        elif action == "video":
            cameraCtl.video(html.escape(form.getfirst("time", "10")))
        elif action == "zoom":
            cameraCtl.zoom(html.escape(form.getfirst("x", "0.0")),html.escape(form.getfirst("y", "0.0")),html.escape(form.getfirst("w", "1.0")),html.escape(form.getfirst("h", "1.0")))
        elif action == "setResolution":
            w = html.escape(form.getfirst("widthRe", ""))
            h = html.escape(form.getfirst("heightRe", ""))
            cameraCtl.setResolution(w,h)
        elif action == "set":
            
            vflip      = html.escape(form.getfirst("vflip", "0"))
            hflip      = html.escape(form.getfirst("hflip", "0"))
            brightness = html.escape(form.getfirst("brightness", "50"))
            exposure_compensation = html.escape(form.getfirst("exposure_compensation", "50"))
            saturation = html.escape(form.getfirst("saturation", "0"))
            sharpness  = html.escape(form.getfirst("sharpness", "0"))
            cameraCtl.set(widthRe,heightRe,vflip,hflip,brightness,exposure_compensation,saturation,sharpness)
        #------res-------
        elif action == "getResPhoto":
            getResPhoto(self)
        elif action == "getResVideo":
            print(self.wfile)
            getResVideo(self)          
        elif action == "delete":
            delete(html.escape(form.getfirst("file", "")))
        elif action == "status":
            cameraCtl.status(self)
        else :
            print("Unknown command: {}".format(action))

            
    def do_GET(self):
        if self.path.startswith('/video/'):
            p1 = threading.Thread(target=takeVideo(self), name="t1", args=["1"])
            p1.start()
        else:
            super().do_GET()

httpd = HTTPServer(server_address, MyHandler)
httpd.serve_forever()

