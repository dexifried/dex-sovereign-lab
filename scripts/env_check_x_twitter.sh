#!/bin/sh
# env_check_x_twitter.sh
# Checks for X API OAuth1 credentials in process env and in /root/.openclaw/workspace/.env
# Does not print credential values — only reports presence/absence.

ENV_FILE="/root/.openclaw/workspace/.env"
MISSING=0
check_key() {
  KEY="$1"
  PRESENT="no"
  # check process environment (POSIX sh doesn't support ${!VAR}, use eval)
  VAL=""
  eval "VAL=\"\$$KEY\""
  if [ "\$VAL" != "" ]; then
    PRESENT="yes (process)"
  fi
  # check .env file
  if [ -f "$ENV_FILE" ] && grep -q "^$KEY=" "$ENV_FILE"; then
    if [ "$PRESENT" = "yes (process)" ]; then
      PRESENT="yes (process + .env)"
    else
      PRESENT="yes (.env)"
    fi
  fi
  if [ "$PRESENT" = "no" ]; then
    echo "$KEY: MISSING"
    MISSING=1
  else
    echo "$KEY: FOUND -> $PRESENT"
  fi
}

check_key X_API_KEY
check_key X_API_SECRET
check_key X_ACCESS_TOKEN
check_key X_ACCESS_SECRET

if [ "$MISSING" -eq 0 ]; then
  echo "All keys present (at least in process env or .env)."
  exit 0
else
  echo "One or more keys missing. Please add them to $ENV_FILE or export them in the shell before retrying."
  exit 2
fi
