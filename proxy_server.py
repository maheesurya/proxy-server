'''
    code for proxy server
'''
import socket
import os
import time
import threading
import sys
from collections import deque
import calendar

lock = threading.Lock()

PORT = 12345
MAX_CACHE = 3
'''
    CACHE deque has a dict of {url, request, date, timeResponse }as its elements
'''
CACHE = deque(maxlen = MAX_CACHE)
HOST = ""

def CacheAppender(obj):
    CACHE.append(obj)

def printURLs(): #prints URLs of requests present in the CACHE memory
    for i in range(len(CACHE)):
        print "URL = ", CACHE[i]['url']

def cache_checker(url): #checks if a particular url and its response is present in the cache or not and returns its index if yes else returns -1
    for i in range(len(CACHE)):
        if CACHE[i]['url'] == url:
            return i
    return -1

def dateTimeChanger(response): #used to change time to localtime from GMT and into the syntax specified in the server code. 
    date = response.split('Date: ')[1:]
    date = date[0].split('\r\n')[0]
    date = time.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
    date = calendar.timegm(date)
    date = time.localtime(date)
    date = time.strftime("%a %b %d %H:%M:%S %Z %Y", date)
    return date

def requestGenerator(DATA):
    REQ = DATA
    DATA = DATA.split()
    filename = DATA[1].split('://')
    if len(filename) != 1:
        filename = filename[1].split(':')
    if len(filename) != 1:
        filename = filename[1].split('/')
    filename = filename[1:]
    filename = '/' + '/'.join(filename)
    REQ = REQ.split(DATA[1])
    REQ = REQ[0] + filename + REQ[1]
    return REQ

def requestHandler(CONN, ADDR):
    DATA = CONN.recv(4096)
    REQ = requestGenerator(DATA)
    DATA = DATA.split()
    #REQ has the customized request for the server socket

    if DATA[0] == 'GET' and DATA[2] == 'HTTP/1.1':
        serverAddr = DATA[4].split(':')
        if len(serverAddr) == 1:
            serverAddr.append(80)
            print "Urls with no ports are not processed and exited"
            sys.exit()

        try:
            proxyClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print serverAddr
            proxyClientSocket.connect((serverAddr[0], int(serverAddr[1])))
        except socket.error:
            print "the Server is not accepting any connections."
            return
        
        if cache_checker(DATA[1]) != -1: #check for the url in cache memory if != -1 then yes else no
            e = cache_checker((DATA[1]))
            print "index in cache", e
            print 'cache has the response object'
            req = CACHE[e]['req'].split('1.1\r\n')      #added the if-modified-since header line
            req = req[0] + '1.1\r\nIf-Modified-Since: ' + CACHE[e]['timeResponse'] + '\r\n' + req[1]
            proxyClientSocket.send(req)
            time.sleep(1)
            resp = proxyClientSocket.recv(100000)
            time.sleep(1)
            splitResp = resp.split()

            dateNew = dateTimeChanger(resp)
            print "DATE NEW", dateNew

            temp = CACHE[e]
            lock.acquire()
            del CACHE[e]
            lock.release()
            printURLs()
            temp['timeResponse'] = str(dateNew)

            if splitResp[1] == '304':
                resp = temp['data']
                print "time changed and 304 has been received"
            elif splitResp[1] == '200':
                temp['data'] = resp
                print "time, data changed and 200 has been received"
            elif splitResp[1] == '404':
                print "404 FILE NOT FOUND, maybe DELETED"
            else:
                print "SOMETHING DIFFERENT HAS HAPPENED"
            CONN.send(resp)

            cacheControl = resp.split('Cache-control: ')
            if 'must-revalidate' in cacheControl[1][0:16] and (splitResp[1] == '304' or splitResp[1] == '200'):
                lock.acquire()
                CACHE.append(temp)
                lock.release()
            elif 'no-cache' in cacheControl[1][0:9]:
                print "not added to cache as no-cache line is present in header" 
            printURLs() 
        
        else:               #cache does not have the object in its memory
            proxyClientSocket.send(REQ)
            time.sleep(1)
            response = proxyClientSocket.recv(100000)
            time.sleep(1)
            CONN.send(response)
            statusCode = response.split()[1]
            date = dateTimeChanger(response)
            
            cacheResp = response.split('Cache-control: ')
            if 'must-revalidate' in cacheResp[1][0:16] and statusCode == '200': #check for binary files or no-cache files
                if len(CACHE) == MAX_CACHE:
                    lock.acquire()
                    CACHE.popleft()  # create space in cache
                    lock.release()
                print "dict added to cache"
                value = dict(url = DATA[1], timeResponse = str(date), data = response, req = REQ)
                lock.acquire()
                CACHE.append(value)
                lock.release()
            elif 'no-cache' in cacheResp[1][0:9]:
                print "NOT ADDED TO CACHE, no cache line present in header"
            elif statusCode == '404':
                print "FILE NOT FOUND"
            else:
                print "SOMETHING DIFFERENT HAS HAPPENED"

            printURLs()
        proxyClientSocket.close()
    else:
        print 'send a proper GET request with http version 1.1'
        # CONN.send('send a proper GET request with http version 1.1')
    CONN.close()
# code starts running from here
if __name__ == '__main__':
    try:
        SOCK = socket.socket()
        SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        sys.stderr.write("[ERROR] %s\n" % msg[1])
        sys.exit(1)

    SOCK.bind((HOST, PORT))
    SOCK.listen(5)

    print 'proxy server started'
    threads = []
    while True:  # Server loop
        CONN, ADDR = SOCK.accept()  # Connect to client
        t = threading.Thread(target = requestHandler,args = (CONN, ADDR))  #use this for threading
        threads.append(t)
        t.setDaemon(True)
        t.start()
