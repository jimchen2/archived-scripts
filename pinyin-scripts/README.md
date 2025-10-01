Change the Chinese ibus-pinyin keyboard: https://github.com/libpinyin/ibus-libpinyin/issues/505

---

```
cd ~/.local/share/applications/
vim org.telegram.desktop._ec1af2dd19574cfd2a7f996f1ceafba7.desktop
sudo chattr +i org.telegram.desktop._ec1af2dd19574cfd2a7f996f1ceafba7.desktop
update-desktop-database ~/.local/share/applications/
```

```
[Desktop Entry]
Name=Телеграм
Comment=Новая эра общения
TryExec=/opt/tsetup.5.15.4/Telegram/Telegram
Exec=/opt/tsetup.5.15.4/Telegram/Telegram -- %u
Icon=org.telegram.desktop
Terminal=false
StartupWMClass=TelegramDesktop
Type=Application
Categories=Chat;Network;InstantMessaging;Qt;
MimeType=x-scheme-handler/tg;x-scheme-handler/tonsite;
Keywords=чат;мессенджер;общение;сообщения;
Actions=quit;
DBusActivatable=true
SingleMainWindow=true
X-GNOME-UsesNotifications=true
X-GNOME-SingleWindow=true

[Desktop Action quit]
Exec=/opt/tsetup.5.15.4/Telegram/Telegram -quit
Name=Выйти из Телеграм
Icon=application-exit
```
