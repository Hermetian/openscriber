Objective

OpenChart is a Whisper/LLAMA wrapper that allows telemedicine practitioners to automatically transcribe their sessions and get summaries suitable for copying into EHR software.

Key principles
1) Easy to install & use
2) HIPAA compliant
-Access control 
-Automatic logout
-All stored patient data encrypted.
3) Runs (slowly, but still functional) on your potato PC

Features

Audio recording
	-Starting point of OpenChart: user simply presses 🟥 to record.
-Runs Whisper transcription concurrently
-Audio logs deleted within 2-7 days of being transcribed
	Saves space
	I don’t want to have to encrypt them
Videogames taught me exactly what happens to people who leave audio diaries just laying around
Transcript management
	-List of transcripts, ordered by time & date
	-Click on any given transcript to expand out
	-Linked to auto summary
		*Shows status of summary if incomplete
		*Enable uploading of audio/video recordings created outside of OpenChart
		*Ability to rerun summary if necessary
Auto summary
	-Starts with some psychiatrist-focused prompts
		Will speak to users to ask about their specific charting needs
Focus on what LLMs can do well (e.g. describe side effects of current medication instead of, say, ‘does patient exhibit any new disorders)
	-User can create, edit, and save prompts
	-Prompts auto-run in background if not already executed
	-Button to rerun prompts if necessary
	-Ability to edit output in-line
	-One-button copy of output

System Reqs

Windows or Mac, 16Gb RAM, integrated or non-performant video card
	-Likely will be building in Electron
