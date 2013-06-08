'''
Created on 11/08/2012

@author: mazkolain
'''
from spotify import LibSpotifyError
from spotify.albumbrowse import Albumbrowse, AlbumbrowseCallbacks
from threading import Event



class LoadTimeoutError(LibSpotifyError):
    pass



class LoadAlbumCallbacks(AlbumbrowseCallbacks):
    __event = None
    
    
    def __init__(self):
        self.__event = Event()
    
    
    def albumbrowse_complete(self, albumbrowse):
        self.__event.set()
    
    
    def wait(self, albumbrowse, timeout=None):
        if not albumbrowse.is_loaded():
            self.__event.wait(timeout)
        
        return albumbrowse.is_loaded()



def load_albumbrowse(session, album, timeout=5, ondelay=None):
    
    #Check a valid number on timeout
    if timeout <= 1:
        raise ValueError('Timeout value must be higher than one second.')
    
    callbacks = LoadAlbumCallbacks()
    albumbrowse = Albumbrowse(session, album, callbacks)
    
    #Wait a single second for the album
    if callbacks.wait(albumbrowse, 1):
        return albumbrowse
    
    #It needs more time...
    else:
        
        #Notify about the delay
        if ondelay is not None:
            ondelay()
        
        #And keep waiting
        if callbacks.wait(albumbrowse, timeout - 1):
            return albumbrowse
    
        else:
            raise LoadTimeoutError('Albumbrowse object failed to load')
