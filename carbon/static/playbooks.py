# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
    carbon.static.playbooks

    A module containing string representations of playbooks used by carbon.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

SYNCHRONIZE_PLAYBOOK = '''
- name: fetch artifacts
  hosts: "{{ hosts }}"

  tasks:
    - name: install rsync
      package:
        name: rsync
        state: present
      become: true

    - name: fetch artifacts
      synchronize:
        src: "{{ item[1] }}"
        dest: "{{ dest }}/{{ hostvars[item[0]]['ansible_hostname'] }}/"
        mode: pull
        recursive: yes
      with_nested:
        - "{{ inventory_hostname }}"
        - "{{ artifacts }}"
'''

GIT_CLONE_PLAYBOOK = '''
- name: clone git repositories
  hosts: "{{ hosts }}"

  tasks:
    - name: install git
      package:
        name: git
        state: present
      become: true

    - name: clone gits
      git:
        repo: "{{ item.repo }}"
        version: "{{ item.version }}"
        dest: "{{ item.dest }}"
      with_items:
        - "{{ gits }}"
'''

ADHOC_SHELL_PLAYBOOK = '''
- name: run shell and fetch results
  hosts: "{{ hosts }}"

  tasks:
    - name: shell command
      shell: "{{ xcmd }}"
      register: sh_results
      ignore_errors: true
      {{ args }}
      {{ options }}

    - name: copy results to file
      shell:
        echo "('{{ inventory_hostname }}', {{ sh_results.rc }}, '{{ sh_results.stderr }}')" >> shell-results.txt
      delegate_to: localhost
'''

ADHOC_SCRIPT_PLAYBOOK = '''
- name: run script and fetch results
  hosts: "{{ hosts }}"

  tasks:
    - name: script command
      script: "{{ xscript }}"
      register: scrpt_results
      ignore_errors: true
      {{ args }}
      {{ options }}

    - name: copy results to file
      shell:
        echo "('{{ inventory_hostname }}', {{ scrpt_results.rc }}, '{{ scrpt_results.stderr }}')" >> script-results.txt
      delegate_to: localhost
'''
