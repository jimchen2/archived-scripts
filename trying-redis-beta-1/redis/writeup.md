---
id: 43783f
tags: source-code, database
---

## **What is Redis?**

Redis is an in memory key-value database. Redis is one of the most popular NoSQL databases.

I don't know much about what Redis is, otherwise I wouldn't be looking into it!

When I self hosted Mastodon, Peertube, and Immich back then, they used Redis as the caching layer in front of PostgreSQL.

Actually, if you search "reading redis source code" there are so many of those blogs and books.

Let's start using Redis on my computer. So the LICENSE changed and there was an open source fork called [valkey](https://github.com/valkey-io/valkey).

```
user@fedora ~> sudo systemctl start redis
user@fedora ~> redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> info
# Server
redis_version:7.2.4
server_name:valkey
valkey_version:8.0.2
...
127.0.0.1:6379> SET mykey "Hello World"
OK
127.0.0.1:6379> GET mykey
"Hello World"
127.0.0.1:6379> KEYS *
1) "listx"
2) "class"
3) "counterX"
4) "mykey"
5) "listX"
...
127.0.0.1:6379> DEL mykey
(integer) 1
127.0.0.1:6379> DEL listX
(integer) 1
127.0.0.1:6379> EXISTS class
(integer) 1

```

Ok, I actually used Redis before and some keys are still left there. It is an in-memory database that is occasionally dumped to a specific file on disk.

```
127.0.0.1:6379> CONFIG GET save
1) "save"
2) "3600 1 300 100 60 10000"
127.0.0.1:6379> CONFIG GET appendonly
1) "appendonly"
2) "no"
127.0.0.1:6379> CONFIG GET dir
1) "dir"
2) "/var/lib/valkey"

```

So it's stored in `/var/lib/valkey/dump.rdb`, dumped there every once in a while.

Some random commands

```
127.0.0.1:6379> LPUSH newlist "item1"
(integer) 2
127.0.0.1:6379> RPUSH newlist "item2" "item3"
(integer) 4
127.0.0.1:6379> LRANGE newlist 0 -1
1) "item1"
2) "item1"
3) "item2"
4) "item3"
127.0.0.1:6379> LPOP newlist
"item1"

```

## **Downloading the Source Code**

We go to the [releases page](https://download.redis.io/releases/). Let's download the earliest release because I am lazy and it's the smallest. It is called "redis-beta-1.tar.gz".

It is written and maintained by someone called Salvatore Sanfilippo, Aka 'antirez', from Italy. He also has a [blog](https://antirez.com/). He is a writer and writes novels along with coding.

And here it is, a small, elegant piece of code, 7 files total. Redis used a file `test-redis.tcl` for its tests. I never used tcl for programming before. Turns out it's also created by this person Salvatore Sanfilippo.

```
user@fedora ~/D/redis> find . -name "*.[c]" | xargs wc -l|sort -n
 211 ./anet.c
 257 ./adlist.c
 318 ./ae.c
 325 ./sds.c
 532 ./picol.c
 547 ./dict.c
1796 ./redis.c
3986 total
```

## **Compiling and Running**

The `make` works out of the box and you get a server

```
user@fedora ~/D/redis> ./redis-server
- Server started
- The server is now ready to accept connections
. 0 clients connected

```

But there are no standalone client files in this version. In the `redis-1.0` there is a file called `redis-cli.c`.

The README said you can connect using `telnet`.

```
user@fedora ~/Code> telnet localhost 6379
Trying ::1...
telnet: connect to address ::1: Connection refused
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
set foo 3
bar
+OK
GET foo
3
bar

```

So the effect is to set the key "foo" to the value "bar"

There are many more examples in the README.

## **What is the Role of the Different Files?**

At its core, Redis is just a key-value database. However, the “value” can be versatile, including sets, lists, etc, think Javascript Objects.

We can look at `redis.c`, the longest and main file, and in the included comments we can roughly know what these files are for.

```
#include "ae.h" /_ Event driven programming library _/
#include "sds.h" /_ Dynamic safe strings _/
#include "anet.h" /_ Networking the easy way _/
#include "dict.h" /_ Hash tables _/
#include "adlist.h" /_ Linked lists _/
```

I began to feel the elegance of this codebase. So there are 5 files for different functionality and the main file `redis.c`. Anyway, any file you look at, you can feel how the code is exceptionally well organized.

`anet.c` is a simplified wrapper for standard functions of client-server communication.

`dict.c` is the main storage for the database. So when you push a key-value pair into Redis, it stores a mapping of the key (sdsstring) to a redisObject.

`adlist.c` stores the list type data inside the Redis database, and some internal server management purposes.

There is also a file called `picol.c`. The file picol.c is a minimal Tcl interpreter, self-contained in the repo, and the Tcl file is used for testing.

All the functions in each file have the file name prefix. So in `redis.c` you can easily know where the functions are.


