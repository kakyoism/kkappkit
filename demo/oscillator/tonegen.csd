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

instr 1
    ; Listen for OSC messages
    kFreqChanged OSClisten giHandle, "/frequency", "f", gkFreq
    kGainChanged OSClisten giHandle, "/gain", "f", gkGainDB
    kWaveChanged OSClisten giHandle, "/oscillator", "i", gkWaveType
    kPlayChanged OSClisten giHandle, "/play", "i", gkPlay
    kStopChanged OSClisten giHandle, "/stop", "i", gkStop

    ; Play/Stop logic
    if changed(gkPlay) == 1 then
        if gkPlay == 1 then
            event "i", 10, 0, -1  ; Infinite duration
        else
            turnoff2 10, 0, 0
        endif
    endif
endin

instr 10 ; Oscillator with waveform switching
    kWaveType = int(gkWaveType)  ; Ensure kWaveType is an integer
    if kWaveType == 0 then
        aOut poscil ampdbfs(gkGainDB), gkFreq, 1  ; Sine Wave
    elseif kWaveType == 1 then
        aOut vco2 ampdbfs(gkGainDB), gkFreq, 10  ; Square Wave
    elseif kWaveType == 2 then
        aOut vco2 ampdbfs(gkGainDB), gkFreq, 12  ; Sawtooth Wave
    endif
    outs aOut, aOut
endin

</CsInstruments>
<CsScore>
f1 0 16384 10 1  ; Sine wave
f2 0 16384 10 1 0 0.5 0.5 0 0.5 -0.5 0 -0.5  ; Square wave
f3 0 16384 10 1 0 1 999 1  ; Sawtooth wave
i1 0 z  ; Start the OSC listener
</CsScore>
</CsoundSynthesizer>
