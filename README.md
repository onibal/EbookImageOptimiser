# EbookImageOptimiser descriptions
Batch image processor to optimise images, for an e-book screensaver. Unused e-book can be used as photo display in the house, as screensavers. One issue is that without light from e-book, the photo are gray, dark (especially on Kobo Libra Colour).

This app take a folder of photos, and process them to make it as nice as possible. Features are:
- Crop: Maximise photo size based on e-book resolution.
- Avoid face cropping: Use face detection to make the best crop position.
- Rotation: Make the photo the good orientation. This depend on how the e-book is position when unused.
- Exposure, Saturation, Contrast: Compensate the lack of brighness and color on the display of the e-book on screensaver mode.

![README-Screenshot](https://github.com/user-attachments/assets/f77a304a-b64c-485f-83b7-1d0f176ef0e9)
[Uploading README-Screenshot.jpg…]()

# Developper Scripts!

- scripts\setup_env.bat: Install modules inside the project
- scripts\build_exe.bat: Build a exe file
