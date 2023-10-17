<CsoundSynthesizer>
<CsOptions>
-odac     ;;;realtime audio out
</CsOptions>
<CsInstruments>

sr = 44100
ksmps = 32
nchnls = 2
0dbfs = 1


; Global OSC listener
gilisten  OSCinit   10000
gkfreq init 440
gkgaindb init -12
gkwavetype init 0  ; GUI option menu is 0-based.
gkwavetypeprev init 0  ; GUI option menu is 0-based.
gkinstr init 10
gkdur init 6
gkstop init 0
gkplay init 0
gkquit init 0
giloopinf init -1

instr 1
kk OSClisten gilisten, "/frequency", "f", gkfreq
kk OSClisten gilisten, "/gain", "f", gkgaindb
kk OSClisten gilisten, "/oscillator", "i", gkwavetype
kk OSClisten gilisten, "/duration", "f", gkdur
kk OSClisten gilisten, "/play", "i", gkplay
kk OSClisten gilisten, "/stop", "i", gkstop
kk OSClisten gilisten, "/quit", "i", gkquit


if gkquit == 1 then
	event "i", 999, 0, 0.01
endif 

if gkstop == 1 then
	turnoff2 gkinstr, 0, 1
	gkstop = 0
endif

if gkwavetype != gkwavetypeprev then  ; turn off current instr and auto-play the new instr
	turnoff2 gkinstr, 0, 0.5
	; gkstop = 1
	gkplay = 1
endif

if gkwavetype == 0 then
	gkinstr = 10
elseif gkwavetype == 1 then
	gkinstr = 20
elseif gkwavetype == 2 then
	gkinstr = 30
elseif gkwavetype == 3 then
	gkinstr = 40
endif

if gkplay == 1 then
	event "i", gkinstr, 0, giloopinf  ; call instr N
	; String sprintfk {{i %d 0 z}}, gkinstr
	; scoreline String, 1
	gkwavetypeprev = gkwavetype
	gkplay = 0
endif

endin

; CAUTION:
; f-table is i-time. so we cannot change ifn on the fly.
; Switch instr instead.

instr 10
a1 poscil ampdb(tonek(gkgaindb, 10)), gkfreq, 1
outs a1, a1
endin

instr 20
a1 poscil ampdb(tonek(gkgaindb, 10)), gkfreq, 2
outs a1, a1
endin

instr 30
a1 poscil ampdb(tonek(gkgaindb, 10)), gkfreq, 3
outs a1, a1
endin

instr 40
a1 poscil ampdb(tonek(gkgaindb, 10)), gkfreq, 4
outs a1, a1
endin

instr 999
	exitnow 0
endin


</CsInstruments>
<CsScore>
f 1 0 4096 10 1
; f 2 0 4096 7 0 1024 1 1024 0 1024 -1 1024 0  ; GEN07, triangle
f 2 0 16384 10 1 0 -0.111 0 0.04 0 -0.020408 0 0.012345679  ; GEN10, triangle
f 3 0 16384 10 1 0 0.3 0 0.2 0 0.14 0 .111  ; GEN10, square
f 4 0 16384 10 1 0.5 0.3 0.25 0.2 0.167 0.14 0.125 .111  ; GEN07, sawtooth by line segments, ramp 0~1 by 2048samp, then drop to 0, ...
i 1 0 z
e
</CsScore>
</CsoundSynthesizer>
