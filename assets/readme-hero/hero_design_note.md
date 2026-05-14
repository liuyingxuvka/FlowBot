# FlowBot README Hero Design Note

## Project Summary

FlowBot is a lightweight Codex skill and local runtime that turns an explicit user request into a FlowGuard-backed linear work route, then executes it through Router, relay-only Controller, PM, Worker, letters, evidence, and review.

## Target Users

Developers and AI-agent users who want a smaller model-first work loop than FlowPilot for explicit long or repeated tasks.

## Core Problem

Ordinary chat plans can drift when a task has many ordered steps. FlowBot makes the route, current node, evidence, review, retry, and completion state explicit.

## Core Workflow

User request -> PM FlowGuard route model -> one-direction linear route -> Router dispatches current letter -> Worker evidence -> PM review -> pass, repair, pause, or done.

## Hero Tagline

A lightweight FlowGuard-backed work loop for turning explicit AI tasks into one executable route.

## Visual Concept

The image shows a request card entering a modeling gate, a finite-state topology compressing into a single bright route, and envelope-like work letters moving through execution and review stations to a final report.

## Image Keywords

FlowGuard topology, linear route, sealed work letters, Router cadence, PM review, lightweight AI work loop, warm white technical product render.

## File Paths

- `assets/readme-hero/hero.png`
- `assets/readme-hero/hero_prompt.md`
- `assets/readme-hero/hero_design_note.md`

## README Insertion Position

The hero block is inserted after the top `# FlowBot` heading and before the English-first language note.
