I didn't have the Macbook Air anymore :))) I now use a ThinkPad

# MacBookAirConfig

This repo is for my configuration files for MacBook Air 15 inch 2023.

- **Why MacBook?** MacBook Air vs. Darter Pro: Key Factors
  - **Battery Life:** MacBook Air wins (over 10h vs. <4h)
  - **Hardware:** MacBook Air: longevity; Darter Pro have Random hardware bugs(keyboard issues, unresponsive touchpad), gets dirty easily, and repairs can be more complex due to company in Colorado.
  - **Thermals:** MacBook Air stays cool.
  - **Software:** MacBook: Proprietary, No ArchLinux, No Mic. System76: Source Code on Github, native Linux
  - **Weight:** 1.5kg vs. 1.66kg
  - **Noise:** MacBook Air is quiet.
  - **Brand:** System76 is more expensive on average, but less recognized
- **Downloading Installer for Asahi(in China)**
  So the files are not available in China, just download and upload them to a S3 bucket (hopefully available in China), then change the urls in the installing script(alx.sh file and installer json file)
- **Enabling Fn**
  MacBook has this annoying feature where you need to press alt+fn+f4(closing) or alt+f2(renaming), so Change this file `/etc/modprobe.d/keyboard.conf`, then `sudo dracut --regenerate-all --force`
- **Remaping Other Keys**
  Use evremap, Move the executable, then Create a systemd service, then remap with toml config in `/etc/evremap/config.toml` (in this repo)
- **Removing Gnome Bloatware**
  <image src="https://github.com/jimchen2/MacBookAirConfig/assets/123833550/8b5914dc-80c3-4821-a8c4-5fb96cdbd980" Width="30%"/>
- **Setting Gnome Shortcuts**
  `ctrl+alt+t`, `ctrl+e`, `super+d`, `alt+tab`, `super+tab` ...
- **Disable While Typing**
  See the seperate folder in this git repo. Use python `evdev` to capture and gsettings to disable.
- **Clash Verge**
  Bypass UFW, See the zip file, I compiled clash verge in the zip file.
