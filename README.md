# Generasia

**Project Website**: [http://Generasia.net]

## Overview

Generasia is an AI music composition project that leverages LLM's understanding and creative capabilities, based on traditional composition concepts like voice parts, orchestration, notation, and counterpoint. Unlike AI music generation products such as SUNO, Generasia establishes a relationship between human operators and LLM more akin to that of inspiration and composer - humans provide prompts to the LLM, while all specific compositions are independently implemented by the LLM after receiving these prompts.

## Core Setup

### 1. Human+AI: Composition Data Generation Hub
The core component of Generasia is a "composition data generation hub" consisting of human operators and LLM. Human operators send creative prompts to the LLM, which then generates AbletonOSC-format note data after comprehension. This phase corresponds to the "writing" stage in human music creation.

### 2. Data+Notes: Data Transmission Middleware
The second component is the data transmission tool. After the LLM generates AbletonOSC-format note data, a program is needed to send this data to Ableton Live, automatically create MIDI tracks, and convert the data into MIDI notes. This phase corresponds to the "musician preparation" stage in human music creation.

### 3. Instruments+Performance: Playback System
The third component is the performance and playback system. When all MIDI tracks and notes are ready, they need to be performed through Ableton Live. In Generasia, we've built a complete system with dozens of analog synthesizers and speakers to simulate a small symphony orchestra in the human world, corresponding to the "performance" stage.

### 4. Recording+Production: Audio Recording, Mixing & Mastering System
The fourth component is the traditional music recording and production system. We've established a mature recording setup using multiple microphones and complete music production software/hardware for post-production, equivalent to the "mixing and mastering" stage in human music creation.

Through these four components, Generasia achieves the entire workflow from AI music creation to final record production.

## Tools

### 1. Composition
All compositions in Generasia were created between May 2024 and January 2025 using Anthropic's Claude Sonnet 3.5 model - meaning every single note was composed by this model.

### 2. Transmission
To transmit data to Ableton Live, we referenced the YouTube video ["How to Connect ChatGPT to Ableton for Automatic AI Music Making"](https://www.youtube.com/watch?v=-sKXN4NrFuY&ab_channel=BurnedGuitarist) and created complete program code (`midi_controller_v.4.py` and `retinfo`) using AbletonOSC as the communication tool. Special thanks to Burned Guitarist for the original video. (Note: We're not professional programmers, so the code might not be optimal.)

### 3. Performance & Playback
You can use any software instrument to play the notes and listen through stereo speakers or headphones. In Generasia, we used:
- MIDI hubs: 1×8-channel and 1×3-channel
- Analog synthesizers: 
  - Moog Model D, Voyager, Matriarch, Grandmother
  - Roland Juno60
  - Sequential Prophet600
  - Yamaha CS20m
  - Korg Arp Odyssey
  - 2×Vermona Perfourmer
  (Total: 10 synths, 16 voices)
- Speaker system:
  - Genelec: 2×8351, 2×8341, 8×8020, 4×8010
  (Total: 16 speakers)
- Connected via Ferrofish Pulse 16dx
Each synthesizer simulates a real instrument, and every sound you hear comes from this system.

### 4. Recording, Mixing & Mastering
You can use any equipment for recording, mixing and mastering. In Generasia, we used:
- Microphones:
  - Neumann KU100
  - AKG C414
  - AKG C451b
  - Shure SM57
- Recording: Lynx Aurora n (with preamp module)
- Mixing/Mastering:
  - Software: FabFilter series
  - Hardware: 
    - API 5500
    - Kush Clariphonic
    - Neve Master Bus Processor
    - Thermionic Culture Vulture 20th Anniversary

## Usage Guide

### 0. Environment Setup
1. Ableton Live 10 or newer
2. AbletonOSC following instructions: [AbletonOSC GitHub](https://github.com/ideoforms/AbletonOSC?tab=readme-ov-file)
3. Python environment with required libraries
4. Download the ‘midi_controller_v.4’ and ‘retinfo’ files

### 1. Generate Note Data
Generate AbletonOSC-format note data through prompts in the LLM. We strongly recommend generating by measures rather than all at once, as our experiments show measure-by-measure generation produces better results.

### 2. Prepare Data
Copy the note data into the `retinfo` document. We use 16 voices, so the final document will contain complete note data for all 16 voices. Adjust according to your own voice count.

### 3. Run Controller
Run the `midi_controller_v.4.py` program.

### 4. View in Ableton
In Ableton Live's Session View, you'll see:
- Automatic BPM changes
- Automatic generation of MIDI clips and notes

### 5. Perform
Play the generated notes.

## Closing Thoughts
While new AbletonOSC based tools like Ableton MCP have emerged (as of March 2025), and more may come in the future, Generasia remains uniquely special to us as our initial pursuit of technology and art integration. 

**Homage** to our inspirational musicians:  
Richard Wagner, Igor Stravinsky, Wendy Carlos.
