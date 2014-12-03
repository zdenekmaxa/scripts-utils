"""
Automatic tweeter, sender to twitter.

Program runs fortune linux program and chooses words radomly to create
random final messages. Those are posted to twitter in the form of total
non-sense. And real twitter accounts do follow that ...

Check https://twitter.com/CompAidedPoetry

Number of per day messages to twitter is limited, twitter stops receiving
messages after some threshold is exceeded.

"""


import time
from subprocess import Popen
from multiprocessing import Process
from tempfile import TemporaryFile
import random
import signal
import twitter


class SignalTermination(Exception):
    pass


class Tweeter(object):
    
    # seconds, twitter supports 100 calls / 60min - says officially, but with
    # 40s delay between each post, after a few hours (2-3?), there is an error
    # max. -daily- update limit has been exceeded
    # in fact a random delay will be done (half, until max. value below)
    DELAY = 600  
    MSG_MAX_LENGTH = 130
    MSG_MAX_LENGTH_HARD = 140
    SOURCE_PROGRAM = "fortune"
    FORTUNE_SOURCE_ITERATIONS = 3
    DATETIME_FORMAT = "%Y-%M-%d %H:%M:%S, %a"
    TWITTER_USER = "CompAidedPoetry"
    # take from tweeter_access_credentials file
    API_KEY = ""
    CONSUMER_KEY = ""
    CONSUMER_SECRET = ""
    ACCESS_TOKEN_KEY = ""
    ACCESS_TOKEN_SECRET = ""
    MIN_WORD_LENGTH = 2
    FORBIDDEN = ("--",
                 ".",
                 "!",
                 "?",
                 ",",
                 "*",
                 "'s",
                 "n't",
                 "...",
                 ";",
                 "[",
                 "]",
                 "(",
                 ")",
                 "{",
                 "}",
                 "'ll",
                 ":",
                 '"',
                 "'ve",
                 "william",
                 "shakespeare",
                 "twain",
                 "'")

    def __init__(self):
        # starts either from 1 or from the message index read from the
        # twitter posts
        self._msgCounter = 1
        self._sendPosts = []

        print "connecting to twitter ..."    
        self.twitter = twitter.Api(consumer_key=self.CONSUMER_KEY,
                                   consumer_secret=self.CONSUMER_SECRET,
                                   access_token_key=self.ACCESS_TOKEN_KEY,
                                   access_token_secret=self.ACCESS_TOKEN_SECRET)
        print "verifying twitter connection:"
        verif = self.twitter.VerifyCredentials()
        print verif
        self._msgCounter = verif.statuses_count
        print "message counter set to '%s'" % self._msgCounter
        signal.signal(signal.SIGHUP, self._signalHandler)
        signal.signal(signal.SIGTERM, self._signalHandler)

    def _signalHandler(self, sigNum, frame):
        m = "signal '%s' received" % sigNum
        print "raising signal exception ..."
        raise SignalTermination(m)

    def _getTimeStamp(self):
        now = time.localtime()
        dt = time.strftime(self.DATETIME_FORMAT, now)
        return dt

    def _checkWord(self, w):
        if len(w) < self.MIN_WORD_LENGTH:
            return False
        for forbid in self.FORBIDDEN:
            if w.find(forbid) >= 0:
                return False
        else:
            return True

    def _getFortuneOutput(self):
        """
        Returns set of words, no white spaces, stripped of unwanted
        start characters like '--', etc.

        """
        output = TemporaryFile("w+")
        for i in range(self.FORTUNE_SOURCE_ITERATIONS):
            proc = Popen(self.SOURCE_PROGRAM, stdout=output)
            returncode = proc.wait()
            output.write("\n")
            
        output.seek(0)

        words = set()
        for line in output:
            for w in line.split():
                w = w.strip().lower()
                if self._checkWord(w):
                    words.add(w)
        output.close()
        return words

    def _getMsg(self):
        msgWords = list(self._getFortuneOutput())
        r = ""
        while len(r) < self.MSG_MAX_LENGTH and len(msgWords) > 0:
            chosen = random.randint(0, len(msgWords) - 1)
            r += "%s " % msgWords.pop(chosen)
        return r.strip()

    def _getLatestPosts(self, nPosts=1):
        try:
            statuses = self.twitter.GetUserTimeline(screen_name=self.TWITTER_USER,
                                                    count=nPosts)
            return statuses
        except twitter.TwitterError, ex:
            print ex

    def _sendPost(self, msg):
        try:
            status = self.twitter.PostUpdate(msg)
        except twitter.TwitterError, ex:
            print ex
        #print status

    def _checkPreviousPost(self, msg):
        """
        Previous post should agree to 'msg'.

        """
        print "%s checking previous post ..." % self._getTimeStamp()
        ss = self._getLatestPosts(nPosts=1)
        print "'%s' == '%s'" % (msg, ss[0].text)
        if ss[0].text != msg:
            return False
        else:
            return True
    
    def _postsSender(self, startIndex):
        counter = startIndex
        msg = ""
        try:
            while True:
                # non-reliable, sometimes, inspite of the long delay still
                # retrieves the post before last ...
                """
                if msg:
                    if not self._checkPreviousPost(msg):
                        print "does not agree, finish."
                        break
                """
                counter += 1
                post = self._getMsg()
                msg = "[%s] %s." % (counter, post)
                if len(msg) >= self.MSG_MAX_LENGTH_HARD:
                    msg  = "%s." % msg[:msg.rfind(' ')]
                print "%s sending: '%s' ..." % (self._getTimeStamp(), msg)
                self._sendPost(msg)
                delay = random.randint(self.DELAY / 2, self.DELAY)
                time.sleep(delay)
                print "waiting %s [s] ..." % delay
        except KeyboardInterrupt:
            print "terminating, KeyboardInterrupt"
        except SignalTermination, ex:
            print "terminating, exception caught:", ex
            
    def start(self):
        self.proc = Process(target=self._postsSender,
                            args=(self._msgCounter,))
        try:
            self.proc.start()
            self.proc.join()
        except KeyboardInterrupt:
            print "KeyboardInterrupt"
            print "terminating ..."
            self.proc.terminate()
        except SignalTermination, ex:
            print ex
            print "terminating ..."
            self.proc.terminate()
        

def main():
    t = Tweeter()
    t.start()


if __name__ == "__main__":
    main()