; This AutoIt script runs main.py silently with no visible CMD window
; Create/overwrite log file with timestamp for the start of execution
$logFile = FileOpen("Logfile\Location", 2) ; 2 = overwrite mode
FileWriteLine($logFile, "=== AutoIt Execution Log ===")
; Format start time in 12-hour format with AM/PM
$hour = @HOUR
$ampm = "AM"
If $hour >= 12 Then
    $ampm = "PM"
    If $hour > 12 Then
        $hour = $hour - 12
    EndIf
EndIf
If $hour = 0 Then $hour = 12 ; Handle midnight (0 hour)
; Format minutes and seconds with leading zeros if needed
$minute = @MIN
If $minute < 10 Then $minute = "0" & $minute
$second = @SEC
If $second < 10 Then $second = "0" & $second
; Write formatted start time to log
FileWriteLine($logFile, "Start Time: " & @YEAR & "-" & @MON & "-" & @MDAY & " " & $hour & ":" & $minute & ":" & $second & " " & $ampm)
FileWriteLine($logFile, "Working Directory: " & @WorkingDir)
; Set the working directory to where main.py is located
FileChangeDir("C:\Users\nepal\Documents\Python Share Apply")
FileWriteLine($logFile, "Changed Working Directory to: " & @WorkingDir)
; Log the command being executed
FileWriteLine($logFile, "Executing Command: " & @ComSpec & ' /c python main.py')
; Run Python script completely hidden
$pid = Run(@ComSpec & ' /c python main.py', "Python\File\Location\Here", @SW_HIDE)
FileWriteLine($logFile, "Process Started with PID: " & $pid)
; Optional: Wait until the script is done (uncomment if needed)
; ProcessWaitClose("python.exe")
; FileWriteLine($logFile, "Python process completed")
; Format end time in 12-hour format with AM/PM
$hour = @HOUR
$ampm = "AM"
If $hour >= 12 Then
    $ampm = "PM"
    If $hour > 12 Then
        $hour = $hour - 12
    EndIf
EndIf
If $hour = 0 Then $hour = 12 ; Handle midnight (0 hour)
; Format minutes and seconds with leading zeros
$minute = @MIN
If $minute < 10 Then $minute = "0" & $minute
$second = @SEC
If $second < 10 Then $second = "0" & $second
; Write formatted end time to log
FileWriteLine($logFile, "End Time: " & @YEAR & "-" & @MON & "-" & @MDAY & " " & $hour & ":" & $minute & ":" & $second & " " & $ampm)
FileClose($logFile)
