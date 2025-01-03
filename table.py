import matplotlib.pyplot as plt
import numpy as np
from midiutil import MIDIFile

def map_value(value, min_val, max_val, min_res, max_res):
    result = min_res + (value - min_val)/(max_val - min_val)*(max_res - min_res)
    return result

def map_value_int(value, min_val, max_val, min_res, max_res):
    result = min_res + (value - min_val)/(max_val - min_val)*(max_res - min_res)
    return result.astype(int)

#extract julian date and tidal component from datafile
def parse_data(filename):
    file = open(filename, mode = 'r')
    lines = file.readlines()
    julianDate = []
    tidalComp = []

    for line in lines:
        data = line.split()
        julianDate.append(float(data[0]))
        tidalComp.append(float(data[9]))

    j = np.array(julianDate)
    t = np.array(tidalComp)
    return j,t

#create a plot of t vs j
def splot(j, t, begin, end):
    jplot = j[begin:end]
    tplot = t[begin:end]
    plt.plot(jplot, tplot)
    plt.xlabel("julian date")
    plt.ylabel("tidal component")
    plt.show()
    print("done")

#create a table synchronized by julian date (unfinished)
def make_table(filenames):
    for file in filenames:
        j, c = parse_data(filenames)

#use difference in tidal component (interval) to calculate next pitch from previous pitch
#using 12 even partitions of the std to determine how much to adjust
#return new pitch, direction, and octave
def alter_pitch(pitch, std, interval):
    octave = 0

    ##### CAREFUL: SCALE STD down to create better variety
    scale_factor = 3
    ######

    step = (std / scale_factor) / 12
    dir = "+"
    #calculate alteration using integer division
    alteration = (int)(interval / step)
    #handle octave transposition
    alteration = pitch + alteration
    octave = (int) (alteration / 12)
    if (alteration > 0):
        alteration = alteration % 12
    else:
        alteration = alteration % -12
    
    if (interval < 0):
        dir = '-'
        
    
    return alteration, dir, octave


    
# take a table of tidal components and julian dates and musify them into compositional parameters! 
def musify(j, c):
    pitches = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    i = 0
    # bin range(c) into octave ranges, expansion by 1 std = 1 octave expansion
    mean = np.mean(c)
    std = np.std(c)

    #rhythms, 0 = slow, 1 = mid, 2 = fast
    rhythm = 0
    
    while (i < len(j)):
        #in a new day! 
        print("\nin a new day! julian date is: ", j[i])
        #first pitch is based on mean
        pitch, dir, octave = alter_pitch(i, std, c[i] - mean)
        print(pitches[pitch], dir, octave, end = '\t')
        #every other pitch in the day
        i = i + 1
        while (not j[i].is_integer()):
            if (i == 0):
                print("start!")
            else:
                #determine speed based on julian date interval 
                if (j[i] - j[i-1] > 0.009):
                    if (rhythm != 0):
                        print("\nslow, j = ", j[i])
                    rhythm = 0
                elif(j[i] - j[i-1] > 0.0005):
                    if (rhythm != 1):
                        print("\nmid, j = ", j[i])
                    rhythm = 1
                elif (j[i] - j[i-1] < 0.0005):
                    if (rhythm != 2):
                        print("\nfast, j = ", j[i])
                    rhythm = 2
                #determine pitch sequence based on tidal component interval
                pitch, dir, octave = alter_pitch(pitch, std, c[i] - c[i-1])
                print(pitches[pitch], dir, octave, end = '\t')
            i = i + 1
            if (i >= len(j)):
                break

def create_blips(j, c, filename, duration, tempo):
    duration_beats = duration
    #constants
    jstart = 60
    jend = 79
    midimin = 0
    midimax = 127
    midiadjust = 50
    #arrays
    time = []
    spiketime = []
    depth = []
    spikedepth = []
    #stats
    bin = 1
    std = np.std(c)
    mean = np.mean(c)
    print(std)
    
    #add timemarkers for midi notes and depth markers that correspond to midi pitch
    for i in range(len(j)):
        if (c[i] - mean > std):
            spiketime.append(j[i])
            spikedepth.append(c[i])
        if (c[i] > mean):
            time.append(j[i])
            depth.append(c[i])


    time = np.array(time)
    spiketime =  np.array(spiketime)
    depth = np.array(depth)
    spikedepth = np.array(depth)


    #scale time to approximate beats and readings to integer MIDI pitches
    t_data = map_value(time, jstart, jend, 0, duration_beats)
    t_depth = map_value_int(depth, np.min(depth), np.max(depth), midimin+midiadjust, midimax - midiadjust)
    spike_data = map_value(spiketime, jstart, jend, 0, duration_beats)
    spike_depth = map_value_int(depth, np.min(depth), np.max(depth), midimin+midiadjust, midimax - midiadjust)

    #print(t_data)

    #MIDI FILE GENERATION

    my_midi_file = MIDIFile(1) 
    my_midi_file.addTempo(track = 0, time = 0, tempo = tempo)
    # add start marker
    my_midi_file.addNote(track=0,channel=0, time=0, pitch = 0, volume=60, duration=2)

    # add in time and spiketime markers
    for i in range(len(t_data)):
        my_midi_file.addNote(track=0,channel=0, time=t_data[i], pitch = t_depth[i], volume=60, duration=2)
    # add readings 0.05 over mean
    for i in range(len(spike_data)):
        my_midi_file.addNote(track=0,channel=0, time=spike_data[i], pitch = spike_depth[i], volume=60, duration=2)

    #add end marker 
    my_midi_file.addNote(track=0,channel=0, time=duration, pitch = 0, volume=60, duration=2)
    #write to file
    with open('data_sound/' + filename + '.mid', "wb") as f:
        my_midi_file.writeFile(f)

def create_blips_multiple(filenames, duration, tempo):
    for f in filenames:
        j, c = parse_data(f)
        f = f[33:42]
        create_blips(j, c, f, duration, tempo)

def main():
    files = open('data_sound/filenames.txt', 'r')
    filenames =  files.read().splitlines()
    realnames = []
    for f in filenames:
        realnames.append('data_20110301to20110320/DARTdata/' + f)
    
    create_blips_multiple(realnames, 600, 110)

    # create_blips(j, c, "51425blips")
  
    # #splot(j, c, 0, len(j))
    
    # filename = 'data_20110301to20110320/DARTdata/dart21413_20110301to20110320_meter.txt'
    # j2, c2 = parse_data(filename)
    # create_blips(j2, c2, "21413blips")
    """

    start = 1800
    stop = 2200

    print("attempting to musify buoy 21418")
    musify(j[start:stop], c[start:stop])
    print()

    plt.plot(j, c, label = "21418")
    # plt.plot(j2, c2, label = "21413")
    # plt.plot(j3, c3, label = "21416")
    # plt.plot(j4, c4, label = "21419")
    plt.xlabel("julian date")
    plt.ylabel("tidal component")
    plt.legend()
    # plt.title("NOAA buoys, near field region, 2011 Tsunami")
    plt.show()
    """
    

if __name__ == "__main__":
    main()