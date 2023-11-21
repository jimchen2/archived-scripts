#!/bin/bash

BASE_DIR=$(pwd)
TENSORBOARD_CMD="tensorboard --logdir_spec="

cd "$BASE_DIR" || exit 1

for DIR in */ ; do
    NAME=$(basename "$DIR")
    TENSORBOARD_CMD+="${NAME}:./${DIR},"
done

TENSORBOARD_CMD=${TENSORBOARD_CMD%,}
eval "$TENSORBOARD_CMD"
