@echo off
title Let's Ramp installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-LetsRamp.ps1" %*
