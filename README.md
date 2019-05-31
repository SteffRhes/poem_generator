

### TrumPoetry

A small poem generating script, written for the Code Poetry Slam 2019 (https://codepoetry.at/).

The script produces short poems on the basis of Trump's Tweets, by juggling phrases randomly together until some rhyming verses come out.

Why Trump? Well, the script takes text as input and builds rhymes on basis of that. These generated rhymes are not cohorenet, neither in their composition nor in their semantics. So, since the output will be an incoherent mess, why not use incoherent mess as input as well? Hence Trump.


### How it works

Its mechanism is pretty simple: 
1.) Pick a random word out of the trump text corpus
2.) Find a matching word in the same corpus (matching here means that the phonetic endings according to the included CMU dictionary of two given words are similiar)
3.) Return the passages that end with those two words.
4.) repeat this process a few times, then mingle the passages together in an alternating way, approximating verse structures (also with customable verse-lengths to provide a simple way of encoding text rhythms).


### How to run

Download the whole repo and run it with
```
python TrumPoetry.py
```
or if you need to use Python 3 explicitly:
```
python3 TrumPoetry.py
```


### Personal favorites

Here are some of my personal favorites:

> Needs the competition!
> Will the FBI ever recover,
> sent a petition,
> try to distract and cover,
> praised FBI Director,
> decision What is our country coming,
> Comey, the Inspector,
> Democrats are in danger of becoming,
> time biggest,
> my Strongest.
> 
> Us the weakest,
> the speech on immigration last,
> are so focused,
> Brutal and Extended Cold Blast,
> Championship teams recently,
> commitment to our men and women,
> Reserve has incessantly,
> The problem with banker Jamie Dimon,
> serving solitary,
> rebuilt military.	
> 
> Plan For Washington,
> The Democrats, who know Steel,
> Sandman & Covington,
> the system to illegally steal,
> appalled that somebody,
> million phone calls and text messages.
> That affects everybody,
> hostages, or gave five terroist hostages,
> our Trade,
> all betrayed.
> 
> Children, Don, Eric,
> tough on Crime and Borders,
> get cheaper generic,
> remember, he took his orders,
> reviews and polls,
> My Campaign for President was conclusively,
> the Democrat pols,
> a brighter future, we cannot exclusively,
> of drugs,
> prayer rugs.



#### Dependencies & Third parties

The scripts runs on python3, no other code dependencies to my knowledge.

The word-to-phoneme dictionary is provided by the Carnegie Mellon University and available here:
http://www.speech.cs.cmu.edu/cgi-bin/cmudict

The raw tweets from Trump in csv form were provided by the TrumpTwitter Archive:
http://www.trumptwitterarchive.com/archive
