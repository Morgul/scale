# Scale

In simplest terms, scale is an asynchronous framework and event loop for python based on [libuv](https://github.com/joyent/libuv).
What it is _practically_ is an application framework that leverages the same event engine used by
[node.js](http://nodejs.org/) to provide the same level of scalability and concurrency as node, with python instead of
javascript. It's a shift in paradigm for python asynchronous frameworks that, frankly, should have come a long time ago.

## Comparison to Stackless, gevent, Twisted, etc

The major difference between current asynchronous frameworks for python and scale is simply this: we don't require you
to learn any special asynchronous programming structure. You can write a scale application using normal pythonic
application development paradigms. We _do_ provide some useful tools, in the form of our callback decorators, but you're
not require to use them.

### The issues with greenlets and coroutines

In many ways, both greenlets and coroutines are elegant solutions to a rather hard problem. From a theoretical
perspective, they're brilliant. Unfortunately, they're non-standard, difficult to intuit about, and (frankly) hard to
explain to someone who's never encountered them before. It's also been my experience that it's a nightmare to try and
build large applications with them.

### But what about Twisted?

I... don't have a very high opinion of Twisted. It's as far from elegant as any python library I've ever used. It's
powerful, and works great... but I've no intention on using it, thanks. There's really nothing more to say than I don't
like it.

### Relation to node.js

I've been a python guy for much longer than I've even known javascript. It's only in the last year that I've had to
write a lot of node applications professionally. Frankly, the speed of development and easy of entry into the node.js
world is something I've felt is sorely missing from python. Add to that some of the crazy performance that we've been
able to get out of properly tuned applications... python simply can't compete. Luckily, most of node.js' strength comes
from the phenomenal `libuv` library. Which happens to have [python bindings](https://pyuv.readthedocs.org/en/v0.10/index.html).
The rest should be obvious.

It's important to point out, scale is **not** a python port of node. Python has a great standard library already, and
python really is a very different language. Often there are more pythonic, more elegant solutions to some of the problems
the node api attempts to address. And, sometimes, I just plain disagree with the node developers. As such, scale will
retain a high degree of compatibility with node, but it will be it's own unique api.

## Asynchronous Paradigm

In languages like javascript, it's easy to write asynchronous programs; everything takes a callback, and the system
libraries that need to defer those callbacks until after IO has happened can easily do that. Unfortunately, python
doesn't support anonymous (or, more importantly, in-line) functions, so it's much harder to achieve the same thing:

```javascript
function doStuff(fileName, callback) {
    fs.readFile(fileName, function(error, data) {
        callback(error, data);
    });
}
```

```python
def doStuff(fileName, callback):
    def handleData(error, data):
        callback(error, data)

    fs.readFile(fileName, handleData)
```

As you can see, it's not impossible; passing in named functions works just fine. But, it's much less elegant, and long
callback pyramids (which should be avoided, but we all know it happens) are _much_ messier in python. That's why, in
scale, we've come up with a more pythonic solution:


```python
def doStuff(fileName, callback):

    @fs.readFile(fileName)
    def handleData(error, data):
        callback(error, data)

```

This may not seem like a bit change, but it has a lot of implications. Instead of trying to explain all of them, let me
give you an example, assuming a python class that works like node's EventEmitter:

```python
# normal python

foo = EventEmitter()

# Declare event handlers
def on_event1():
    print("Event 1 fired.")

def on_get_bar():
    foo.emit('bar', "This is bar!")

def on_error(error):
    logging.exception('Encountered error: {}'.format(error))

# Register event handlers
foo.on('event1', on_event1)
foo.on('get bar', on_get_bar)
foo.on('error', on_error)
```

```python
# scale style

foo = EventEmitter()

@foo.on('event1')
def cb():
    print("Event 1 fired.")

@foo.on('get bar')
def cb():
    foo.emit('bar', "This is bar!")

@foo.on('error')
def cb(error):
    logging.exception('Encountered error: {}'.format(error))
```

While this isn't earth-shattering, it _is_ an improvement. Our callbacks are more readable, and self-contained. Still,
it's just some minor syntactic sugar that I'm sure can feel more like a style choice than a way to handle asynchronous
callbacks. But let's look at what happens once we actually start calling things asynchronously.

Just like node, simply calling callbacks doesn't gain you asynchronous functionality; it's simply a programming style
that allows node to easily hide the asynchronous boilerplate from you. Scale, as you might expect does the same thing
with it's decorator based callbacks. Let's look at a simple example:

```python
// Declaring an asynchronous function in scale
@asyncFunc
def doStuff(name, callback):
    if name != 'Dave':
        callback(None, 'Welcome, traveler!')
    else:
        callback("I'm sorry Dave, but I can't let you do that.")

// Calling the asynchronous function, with the argument 'Bob'
@doStuff.async('Bob')
def cb(error, msg):
    if error:
        print('Error:', error)
    else:
        print('Message:', msg)
```

In this example, `doStuff.async` actually schedules the `doStuff` function to be called on the next iteration of the
event loop. Here is the same code without using the decorator syntax:

```python
def doStuff(name, callback):
    if name != 'Dave':
        callback(None, 'Welcome, traveler!')
    else:
        callback("I'm sorry Dave, but I can't let you do that.")

def cb(error, msg):
    if error:
        print('Error:', error)
    else:
        print('Message:', msg)

# Schedule doStuff with the event loop.
process.callSoon(doStuff, 'Bob', cb)
```

As you can see, doing things without the decorators can get messy, quickly. If you're still not convinced by this point,
then good news: you don't have to use them if you don't want to.

### Limitations

This is still python. Depending on your perspective, that's either a fortunate thing, or not. Either way, it simply
isn't ever going to be possible to have anonymous function in python, so it will never be practical to do everything as
simply as you do in javascript. The intention of scale, however, is that we will give you as many tools as possible to
keep you code concise, while still being as beautiful asynchronous as our node.js cousins.

## Installing

Simply install with pip or easy install:

```bash
$ sudo pip install scale
```