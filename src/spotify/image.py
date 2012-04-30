'''
Created on 02/05/2011

@author: mazkolain
'''
import ctypes

from _spotify import image as _image

from spotify import DuplicateCallbackError, UnknownCallbackError

from spotify.utils.decorators import synchronized, extract_args

import binascii

from utils.finalize import track_for_finalization
from utils.weakmethod import WeakMethod
import weakref



@synchronized
def create(session, image_id):
    buf = (ctypes.c_char * 20)()
    buf.value = binascii.a2b_hex(image_id)
    ii = _image.ImageInterface()
    
    return Image(
        ii.create(session.get_struct(), buf)
    )


@synchronized
def create_from_link(session, link):
    ii = _image.ImageInterface()
    return Image(
        ii.create_from_link(session.get_struct(), link.get_struct())
    )



class ProxyImageCallbacks:
    __image = None
    __callbacks = None
    __c_callback = None
    
    
    def __init__(self, image, callbacks):
        self.__image = weakref.proxy(image)
        self.__callbacks = callbacks
        self.__c_callback = _image.image_loaded_cb(
            WeakMethod(self.image_loaded)
        )
    
    def image_loaded(self, image_struct, userdata):
        self.__callbacks.image_loaded(self.__image)
    
    def get_c_callback(self):
        return self.__c_callback
    
    def get_callbacks(self):
        return self.__callbacks



class ImageCallbacks:
    def image_loaded(self, image):
        pass



class ImageFormat:
    Unknown = -1
    JPEG = 0



@extract_args
@synchronized
def _finalize_image(image_interface, image_struct):
    image_interface.release(image_struct)
    print "image __del__ called"



class Image:
    __image_struct = None
    __image_interface = None
    __callbacks = None
    
    
    def __init__(self, image_struct):
        self.__image_struct = image_struct
        self.__image_interface = _image.ImageInterface()
        self.__callbacks = {}
        
        #register finalizers
        args = (self.__image_interface, self.__image_struct)
        track_for_finalization(self, args, _finalize_image)
    
    
    @synchronized
    def add_load_callback(self, callback):
        cb_id = id(callback)
        
        if cb_id in self.__callbacks:
            raise DuplicateCallbackError()
        
        else:
            proxy = ProxyImageCallbacks(self, callback)
            self.__callbacks[cb_id] = proxy
            self.__image_interface.add_load_callback(
                self.__image_struct, proxy.get_c_callback(), None
            )
    
    
    @synchronized
    def remove_load_callback(self, callback):
        cb_id = id(callback)
        
        if cb_id not in self.__callbacks:
            raise UnknownCallbackError()
        
        else:
            proxy = self.__callbacks[cb_id]
            self.__image_interface.remove_load_callback(
                self.__image_struct, proxy.get_c_callback(), None
            )
            del self.__callbacks[cb_id]
    
    
    def remove_all_load_callbacks(self):
        for key in self.__callbacks.keys():
            self.remove_load_callback(self.__callbacks[key].get_callbacks())
    
    
    @synchronized
    def is_loaded(self):
        return self.__image_interface.is_loaded(self.__image_struct)
    
    
    @synchronized
    def error(self):
        return self.__image_interface.error(self.__image_struct)
    
    
    @synchronized
    def format(self):
        return self.__image_interface.format(self.__image_struct)
    
    
    @synchronized
    def data(self):
        size = ctypes.c_size_t()
        raw = self.__image_interface.data(self.__image_struct, ctypes.pointer(size))
        dest = ctypes.cast(raw, ctypes.POINTER(ctypes.c_char * size.value))
        return str(buffer(dest.contents))
    
    
    def get_struct(self):
        return self.__image_struct
