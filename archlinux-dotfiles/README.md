Backup

```
backup_dir="$HOME/config_backup" # Set the backup directory
mkdir -p "$backup_dir/.config" "$backup_dir/.local/share" # Create necessary subdirectories

cp -r "$HOME/.config/nvim" "$backup_dir/.config" # Copy Neovim configuration
cp -r "$HOME/.config/fish" "$backup_dir/.config" # Copy Fish configuration
cp -r "$HOME/.config/gtk-2.0" "$backup_dir/.config" # Copy GTK 2.0 configurations
cp -r "$HOME/.config/gtk-3.0" "$backup_dir/.config" # Copy GTK 3.0 configurations
cp -r "$HOME/.config/gtk-4.0" "$backup_dir/.config" # Copy GTK 4.0 configurations
cp -r "$HOME/.local/share/fonts" "$backup_dir/.local/share" # Copy Fonts
cp -r "$HOME/.local/share/backgrounds" "$backup_dir/.local/share" # Copy Background
cp -r "$HOME/.config/dconf/user" "$backup_dir/.config/dconf" # Copy Dconf settings
cp -r "$HOME/.config/hypr" "$backup_dir/.config" # Copy Hyprland configuration
cp "$HOME/.config/user-dirs.dirs" "$backup_dir/.config" # Copy User directories configuration
cp -r "$HOME/.config/nautilus" "$backup_dir/.config" # Copy Nautilus configuration
cp "$HOME/.gitconfig" "$backup_dir" # Copy Git configuratio
```
