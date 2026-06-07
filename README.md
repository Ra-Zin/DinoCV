## Dino CV

Dino CV is a computer vision version of the Chrome Dino game.
Instead of using keyboard controls, the player can control the dinosaur through using body movements that is detected through a webcam.

## Features
- Real-time body tracking using webcam
- Gesture based game control 
- Chrome Dino style gameplay 
- Built using Python and Computer Vision

## How It Works
The system uses a webcam to detect human body (hip) movement. Those movements are then converted into in-game actions like jumping or ducking for dodging obstacles. 
<br><br>
Two lines will appear in the webcam, one at the middle and another at the bottom, which acts as threshold for jumping and ducking.

Example:
- Jump in a way your hip goes above the middle line -> Dino jumps
- Duck in a way your hip goes below the bottom line -> Dino ducks

## Technologies
- Python
- OpenCV (camera processing)
- Mediapipe (body tracking)
- Pygame (game engine)

## Note
To make the game work, you must show your full body. The game will not work if your face goes out from the webcam.

## Author 
Built by Rajin Maharjan