#!/usr/bin/env zsh
                            for i in task.*; do
                                cd ./$i
                                pwd
                                abacus > abacus.out
                                cd ../
                            done
                            