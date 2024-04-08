# -*- coding: utf-8 -*-
"""Pose Estimation Main

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tzw4OlQYwsH00e6w_lAuc24ygW7UH2ul
"""

import cv2
import mediapipe as mp
import numpy as np
from bs4 import BeautifulSoup
import requests
from pytube import YouTube
import os
import langid

def extract_video_url(html_content, search_word):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Find all divs with class 'col-md-6'
    divs = soup.find_all('div', class_='col-md-6')
    for div in divs:
        # Find the <h5> tag within the div
        category_tag = div.find('h5')
        if category_tag and 'रोज़मर्रा/Everyday' in category_tag.text:
            # Find the first video iframe within the target div
            video_iframe = div.find('iframe')
            if video_iframe:
                h4_tag = div.find('h4')
                h4_text = h4_tag.text.strip()
                # Split the text into individual words
                words = h4_text.split()
                print(words)
                # Check each word for language and match with the search word
                for word in words:
                    print(word + " : " + langid.classify(word)[0])
                    # Detect the language of the word

                    if langid.classify(word)[0] == "en":  # Assuming "en" is the language code for English
                        if word == search_word:
                            return video_iframe['src']
                        else:
                          break
    return None



def get_video_url(search_word):
    # URL of the webpage
    url = "https://divyangjan.depwd.gov.in/islrtc/search.php"

    # Send a POST request to search for the word
    search_response = requests.post(url, data={'search': search_word, 'submit': 'Search'})
    video_url = extract_video_url(search_response.content,search_word)
    return video_url


def download_youtube_video(video_url, output_path):

    try:
        # Create a YouTube object
        yt = YouTube(video_url)

        # Get the highest resolution stream
        stream = yt.streams.get_highest_resolution()

        # Download the stream to the specified output path
        downloaded_file_path = stream.download(output_path)

        # Extract filename from the downloaded file path
        filename = os.path.basename(downloaded_file_path)
        print("Video downloaded successfully. Filename:", filename)
        return filename
    except Exception as e:
        print("Error:", str(e))
        return None


def generate_pose_video(word):
    # Get the video URL for the word
    video_url = get_video_url(word)
    if not video_url:
        print("Video URL not found for word:", word)
        return None

    # Download the video
    downloaded_video_path = download_youtube_video(video_url, './videos')
    if not downloaded_video_path:
        print("Failed to download video for word:", word)
        return None

    # Read the downloaded video
    cap = cv2.VideoCapture("./videos/" + downloaded_video_path)

    # Get the video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define codec and create VideoWriter object for pose video
    output_path = "./videos/pose_" + word + ".mp4"
    fourcc = cv2.VideoWriter_fourcc(*'avc1') # avc1 to avoid codex error change to 'mp4v' if not needed
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Initialize MediaPipe Holistic model
    mp_holistic = mp.solutions.holistic

    # Process the video frame by frame
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Create a black image
            black_image = np.zeros_like(frame)

            # Detect landmarks
            results = holistic.process(image=frame)

            # Draw only the pose landmarks on the black image
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing.draw_landmarks(black_image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            mp_drawing.draw_landmarks(black_image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            mp_drawing.draw_landmarks(black_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)

            # Write the frame to the output video
            out.write(black_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    print("Pose-only video saved successfully for word:", word)
    return output_path

def join_videos(video_paths, output_path):
    # Initialize the VideoCapture objects for all videos
    videos = [cv2.VideoCapture(path) for path in video_paths]

    # Get video properties from the first video
    fps = int(videos[0].get(cv2.CAP_PROP_FPS))
    width = int(videos[0].get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(videos[0].get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define codec and create VideoWriter object for the joined video
    fourcc = cv2.VideoWriter_fourcc(*'avc1') # avc1 to avoid codec error change to 'mp4v' if not needed
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Write frames from each video to the output video
    for i in range(len(video_paths)):
        while videos[i].isOpened():
            ret, frame = videos[i].read()
            if not ret:
                break
            out.write(frame)

    # Release VideoCapture objects and VideoWriter object
    for video in videos:
        video.release()
    out.release()
    print("Videos joined successfully. Output:", output_path)


def generate_final_video(sentence):
    sentence = sentence.title()
    words = sentence.split()
    
    # Generate pose video for each word
    video_paths = [generate_pose_video(word) for word in words]
    print('videopath:',video_paths)
    # Remove None values (indicating failure to generate pose video for a word)
    video_paths = [path for path in video_paths if path]
    final_video_url = "./videos/"+sentence+".mp4"
    # Join the pose videos to form a single video
    join_videos(video_paths,final_video_url)
    return final_video_url