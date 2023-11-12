<CsoundSynthesizer>
<CsOptions>
-odac     ;;;realtime audio out
--port=10001  ; OSC port
</CsOptions>
<CsInstruments>

sr = 44100
ksmps = 32
nchnls = 2
0dbfs = 1

; OSC listener setup
giOSCPort = 10000
giHandle OSCinit giOSCPort

; Global variables
gkFreq init 440
gkGainDB init -9
gkWaveType init 0
gkPlay init 0
gkStop init 0
gkCurrentWave init 0

instr 1
    ; Listen for OSC messages
    kFreqChanged OSClisten giHandle, "/frequency", "f", gkFreq
    kGainChanged OSClisten giHandle, "/gain", "f", gkGainDB
    kWaveChanged OSClisten giHandle, "/oscillator", "i", gkWaveType
    kPlayChanged OSClisten giHandle, "/play", "i", gkPlay
    kStopChanged OSClisten giHandle, "/stop", "i", gkStop

	; Check for waveform change
    if changed(gkWaveType) == 1 && gkPlay == 1 then
        ; Stop current waveform
        turnoff2 gkCurrentWave, 0, 0

        ; Update current waveform
        gkCurrentWave = 10 + gkWaveType

        ; Start new waveform
        event "i", gkCurrentWave, 0, -1
    endif

    ; Play
    if changed(gkPlay) == 1 && gkPlay == 1 then
        gkCurrentWave = 10 + gkWaveType
        event "i", gkCurrentWave, 0, -1
    endif

    ; Stop
    if changed(gkStop) == 1 && gkStop == 1 then
        turnoff2 gkCurrentWave, 0, 0
        gkStop = 0
    endif
endin

instr 10 ; Sine Wave
    aOut poscil ampdbfs(gkGainDB), gkFreq, 1
    outs aOut, aOut
endin

instr 11 ; Square Wave
    aOut vco2 ampdbfs(gkGainDB), gkFreq, 10
    outs aOut, aOut
endin

instr 12 ; Sawtooth Wave
    aOut vco2 ampdbfs(gkGainDB), gkFreq, 12
    outs aOut, aOut
endin

instr 99
    a1 oscili 0.5, 440, 1  ; Simple sine wave at 440 Hz
    outs a1, a1
endin
; Add more waveform instruments here...

</CsInstruments>
<CsScore>
f1 0 16384 10 1  ; Sine wave
f2 0 16384 10 1 0 0.5 0.5 0 0.5 -0.5 0 -0.5  ; Square wave
f3 0 16384 10 1 0 1 999 1  ; Sawtooth wave
i1 0 z  ; Start the OSC listener
</CsScore>
</CsoundSynthesizer>
