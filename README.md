# proxy-server
A multi-threaded HTTP/HTTPS proxy server and a web-server to transfer files.Uses socket programming.

The code has the implementation of a proxy server. It is a NON-PERSISTENT type
It doesn't process requests with no ports in the URL(done purposefully to ignore unnecessary requests like favicon.ico and global websites like google, etc).
Max length of cache is 3. A deque has been used to implement this.
A function with name dateTimeChanger() has been used to change the dateTime to localtime and into the syntax specified in the server.py code.
A function with name requestGenerator() is used to generate a modified request for the socket on the server side to process.
Max length of a response that can be stored is 1e5.
The policy in the Cache memory is FIRST IN FIRST OUT.
A mutex lock has been implemented while modifying CACHE memory
