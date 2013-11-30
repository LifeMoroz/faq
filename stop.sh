#!/bin/bash
echo 'Stopping all related services'
kill $(cat run/*.pid)
echo 'Ok'

