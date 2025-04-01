import os
import openai
import io
import re
import itertools
from sys import exit
from pythonosc import udp_client
import warnings
from openai import OpenAI

import httpx
import random
import time
import pathlib
from typing import List, Optional, Any, Dict, Tuple

# Constants
PITCH = "pitch"
START_TIME = "start_time"
VELOCITY = "velocity"
DURATION = "duration"
SCHEMA = [PITCH, START_TIME, DURATION, VELOCITY]
VALID_MIDI_NOTES = range(0, 127)
SONG_TEMPO = 77

# Ableton OSC client parameters
IP = "127.0.0.1"
PORT = 11000
MELODY = "Melody"
DRUM = "Drum"
BASS = "Bass"

midi_flag: List[str] = []
PROMPT = ""

def generate_random_number() -> int:
    """Generate a random number between 10 and 120."""
    random.seed(time.time())
    return random.randint(10, 120)

def read_txt_file(file_path: str) -> str:
    """Read content from a text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Content of the file as string
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def remove_whitespace(s: str) -> str:
    """Remove all whitespace characters from string.
    
    Args:
        s: Input string
        
    Returns:
        String with whitespace removed
    """
    return re.sub(r'[\r\n\t\f\v]', '', s)

def prepare_midi_data(path: str) -> List[str]:
    """Prepare MIDI data from file.
    
    Args:
        path: Path to MIDI data file
        
    Returns:
        List of cleaned MIDI data lines
    """
    midi_flag_tmp = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = remove_whitespace(line.strip())
            if len(line) > 0:
                midi_flag_tmp.append(line)
    return midi_flag_tmp

def _get_openai_client(use_proxy: bool = False) -> OpenAI:
    """Create and return OpenAI client with optional proxy configuration."""
    if use_proxy:
        return OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.Client(
                base_url=os.getenv("OPENAI_BASE_URL"),
                follow_redirects=True,
            ),
        )
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(prompt: str, model: str = "gpt-4o", use_proxy: bool = False) -> str:
    """
    Get OpenAI API response for the given prompt.
    
    Args:
        prompt: The input prompt
        model: The model to use (default: gpt-4o)
        use_proxy: Whether to use proxy configuration (default: False)
    
    Returns:
        The generated response text
    """
    try:
        client = _get_openai_client(use_proxy)
        
        if model in ["gpt-3.5-turbo-instruct", "text-davinci-003"]:
            response = client.completions.create(
                model=model,
                prompt=prompt,
                temperature=0.9,
                max_tokens=350,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"],
            )
            return response.choices[0].text
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        warnings.warn(f"OpenAI API error: {str(e)}")
        raise

def find_substring(string: str, start: str, end: str) -> str:
    """Find substring between keywords."""
    try:
        s = string.rindex(start + ":") + len(start) + 1
        e = string.rindex(end + ":", s)
        return string[s:e]
    except ValueError:
        return ""

def parse_table_to_list(data: str, valid_midi_notes: List[int]) -> Optional[List[List[str]]]:
    """Convert text table to a 2D array of MIDI data.
    
    Args:
        data: String containing MIDI data in table format
        valid_midi_notes: List of valid MIDI note numbers
        
    Returns:
        2D list of parsed MIDI data, or None if input is empty
    """
    if data:
        data = [
            re.split("\t| ", row)
            for row in data.split("\n")
            if row and any(row.startswith(str(note)) for note in valid_midi_notes)
        ]
        data = [i for i in data if len(i) >= len(SCHEMA)]
        return data
    return None

def calculate_pattern_duration(data: List[List[str]]) -> Optional[float]:
    """Calculate total duration of a MIDI pattern.
    
    Args:
        data: 2D list of MIDI data
        
    Returns:
        Total duration in beats as float, or None if input is empty
    """
    if data:
        t = float(data[0][SCHEMA.index(START_TIME)])
        for row in data:
            duration = float(row[SCHEMA.index(DURATION)])
            t += duration
        return round(t, 4)
    return None

def initiate_loop_clips(ableton_client: udp_client.SimpleUDPClient,
                      midi_list: List[List[List[str]]],
                      index: int) -> None:
    """Initialize Ableton loop clips with MIDI data.
    
    Args:
        ableton_client: OSC client for Ableton Live
        midi_list: List of MIDI data patterns (3D list)
        index: Starting track index
    """
    i = index
    for midi_data in midi_list:
        midi_pattern_len = calculate_pattern_duration(midi_data)
        ableton_client.send_message("/live/clip_slot/delete_clip", (i, 0))
        ableton_client.send_message("/live/clip_slot/create_clip", (i, 0, midi_pattern_len))
        i += 1

def initiate_clips(ableton_client: udp_client.SimpleUDPClient,
                 song_tempo: int,
                 melody_data: List[List[str]],
                 drum_data: List[List[str]],
                 bass_data: List[List[str]]) -> None:
    """Initialize Ableton clips for melody, drum and bass tracks.
    
    Args:
        ableton_client: OSC client for Ableton Live
        song_tempo: Tempo in BPM
        melody_data: Melody MIDI data
        drum_data: Drum MIDI data
        bass_data: Bass MIDI data
    """
    ableton_client.send_message("/live/song/set/tempo", song_tempo)

    melody_pattern_len = calculate_pattern_duration(melody_data)
    drum_pattern_len = calculate_pattern_duration(drum_data)
    bass_pattern_len = calculate_pattern_duration(bass_data)

    ableton_client.send_message("/live/clip_slot/delete_clip", (0, 0))
    ableton_client.send_message("/live/clip_slot/create_clip", (0, 0, melody_pattern_len))

    ableton_client.send_message("/live/clip_slot/delete_clip", (1, 0))
    ableton_client.send_message("/live/clip_slot/create_clip", (1, 0, drum_pattern_len))

    ableton_client.send_message("/live/clip_slot/delete_clip", (2, 0))
    ableton_client.send_message("/live/clip_slot/create_clip", (2, 0, bass_pattern_len))

def send_loop_events(ableton_client: udp_client.SimpleUDPClient,
                   midi_list: List[List[List[str]]],
                   index: int) -> None:
    """Send MIDI note events to Ableton loop clips.
    
    Args:
        ableton_client: OSC client for Ableton Live
        midi_list: List of MIDI data patterns (3D list)
        index: Starting track index
    """
    i = index
    for midi_data in midi_list:
        if not midi_data:
            continue
        pointer = float(midi_data[0][SCHEMA.index(START_TIME)])
        for row in midi_data:
            if row[3].rfind("'") != -1:
                row[3] = row[3].replace("'", "")
            pitch = int(row[SCHEMA.index(PITCH)])
            velocity = int(row[SCHEMA.index(VELOCITY)])
            duration = float(row[SCHEMA.index(DURATION)])
            ableton_client.send_message("/live/clip/add/notes", (i, 0, pitch, pointer, duration, velocity, 0))
            pointer += duration
        i += 1

def send_events(ableton_client: udp_client.SimpleUDPClient,
              melody_data: List[List[str]],
              drum_data: List[List[str]],
              bass_data: List[List[str]]) -> None:
    """Send MIDI note events to Ableton clips.
    
    Args:
        ableton_client: OSC client for Ableton Live
        melody_data: Melody MIDI data
        drum_data: Drum MIDI data
        bass_data: Bass MIDI data
    """
    if melody_data:
        pointer = float(melody_data[0][SCHEMA.index(START_TIME)])
        for row in melody_data:
            if row[3].rfind("'") != -1:
                row[3] = row[3].replace("'", "")
            pitch = int(row[SCHEMA.index(PITCH)])
            velocity = int(row[SCHEMA.index(VELOCITY)])
            duration = float(row[SCHEMA.index(DURATION)])
            ableton_client.send_message("/live/clip/add/notes", (0, 0, pitch, pointer, duration, velocity, 0))
            pointer += duration

    if drum_data:
        pointer = float(drum_data[0][SCHEMA.index(START_TIME)])
        for row in drum_data:
            if row[3].rfind("'") != -1:
                row[3] = row[3].replace("'", "")
            pitch = int(row[SCHEMA.index(PITCH)])
            velocity = int(row[SCHEMA.index(VELOCITY)])
            duration = float(row[SCHEMA.index(DURATION)])
            ableton_client.send_message("/live/clip/add/notes", (1, 0, pitch, pointer, duration, velocity, 0))
            pointer += duration

    if bass_data:
        pointer = float(bass_data[0][SCHEMA.index(START_TIME)])
        for row in bass_data:
            if row[3].rfind("'") != -1:
                row[3] = row[3].replace("'", "")
            pitch = int(row[SCHEMA.index(PITCH)])
            velocity = int(row[SCHEMA.index(VELOCITY)])
            duration = float(row[SCHEMA.index(DURATION)])
            ableton_client.send_message("/live/clip/add/notes", (2, 0, pitch, pointer, duration, velocity, 0))
            pointer += duration

def build_prompt(prompt: str, midi_flag_new: List[str]) -> str:
    """Build the final prompt by replacing placeholders with MIDI flag data.
    
    Args:
        prompt: The template prompt with placeholders
        midi_flag_new: List of MIDI flag strings
        
    Returns:
        The final prompt with placeholders replaced
    """
    prompt = prompt.replace("first-hand", midi_flag_new[0])
    prompt = prompt.replace("x-hand-len", str(len(midi_flag_new)))

    i = 1
    other_hand = ""
    other_hand_and = ""
    while i < len(midi_flag_new):
        other_hand += " ‘" + midi_flag_new[i] + "’ "
        other_hand_and += " and ‘" + midi_flag_new[i] + "’"
        i += 1
    prompt = prompt.replace("other_hand", other_hand)
    prompt = prompt.replace("other-hand-and", other_hand_and)

    i = 0
    loop_hand = ""
    loop_hand_line = ""
    while i < len(midi_flag_new):
        loop_hand += " ‘" + midi_flag_new[i] + ": 60 0.125 0.225 110 …’ "
        loop_hand_line += "‘" + midi_flag_new[i] + ": 60 0.125 0.225 110 …’\n"
        i += 1

    prompt = prompt.replace("loop_hand", loop_hand)
    prompt = prompt.replace("loop-hand-line", loop_hand_line)
    return prompt

def get_midi_flag(input_string: str) -> List[str]:
    """Extract MIDI flags from input string using regex.
    
    Args:
        input_string: The string containing MIDI flags
        
    Returns:
        List of extracted MIDI flag strings
    """
    pattern = r"'([^']*)'"
    matches = re.findall(pattern, input_string)
    return matches

if __name__ == "__main__":
    module_file_path = pathlib.Path(__file__).resolve().parent / 'retinfo'
    ableton_client = udp_client.SimpleUDPClient(IP, PORT)
    SONG_TEMPO = generate_random_number()
    ableton_client.send_message("/live/song/set/tempo", SONG_TEMPO)
    is_first = True
    is_error = False
    is_retry = True
    while True:
        mtime = module_file_path.stat().st_mtime
        time.sleep(3)  # Check file changes every 3 seconds

        if module_file_path.stat().st_mtime != mtime or is_first or is_error:
            response_text = read_txt_file("./retinfo")
            midi_flag_new = get_midi_flag(response_text)
            if not is_error:
                midi_flag_tmp = list(filter(lambda item: item not in midi_flag, midi_flag_new))

            is_first = False
            if len(midi_flag_tmp) > 0 or is_retry:
                if len(midi_flag_tmp) == 0:
                    midi_flag_tmp.extend(midi_flag_new)
                    index = 0
                else:
                    index = len(midi_flag)
                    midi_flag.extend(midi_flag_tmp)

                is_error = False
                for flag in midi_flag_tmp:
                    if flag not in response_text:
                        warnings.warn("Incomplete GPT response. Try again." + flag)
                        is_error = True
                if is_error:
                    midi_flag = list(filter(lambda item: item not in midi_flag_tmp, midi_flag))
                    continue

                midi_list = []
                size = len(midi_flag_tmp)
                i = 0
                while i < size:
                    if i != size - 1:
                        midi_list.append(
                            parse_table_to_list(find_substring(response_text, midi_flag_tmp[i], midi_flag_tmp[i + 1]),
                                                VALID_MIDI_NOTES))
                    else:
                        if response_text.rfind(midi_flag_tmp[i] + ":") != -1:
                            midi_list.append(parse_table_to_list(response_text.split(midi_flag_tmp[i] + ":", 1)[1],
                                             VALID_MIDI_NOTES))
                        else:
                            midi_list.append(parse_table_to_list(response_text.split(midi_flag_tmp[i], 1)[1],
                                             VALID_MIDI_NOTES))
                    i += 1

                if len(midi_list) != size:
                    warnings.warn("Incorrect GPT response MIDI note format. Try again.")
                    midi_flag = list(filter(lambda item: item not in midi_flag_tmp, midi_flag))
                    is_error = True
                    continue
                for midi_data in midi_list:
                    if not midi_data:
                        warnings.warn("Incomplete GPT response. Try again.")
                        is_error = True
                        break
                if is_error:
                    midi_flag = list(filter(lambda item: item not in midi_flag_tmp, midi_flag))
                    continue

                initiate_loop_clips(ableton_client, midi_list, index)
                send_loop_events(ableton_client, midi_list, index)
                print(">>>>> send_loop_events success:" + ';'.join(midi_flag_tmp))
