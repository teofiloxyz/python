package rofi

import (
    "os"
    "os/exec"
    "log"
    "strconv"
    "strings"
)

var MenuMessage string

func SimplePrompt(prompt string) string {
    cmd := "rofi -dmenu -p '" + prompt + "' -l 0 -theme-str 'entry { placeholder: \"\"; } inputbar { children: [prompt, textbox-prompt-colon, entry]; } listview { border: 0; }'" + MenuMessage
    output, err := exec.Command("bash", "-c", cmd).Output()
    if err != nil {
        log.Fatal(err)
    }

    return strings.TrimSuffix(string(output), "\n")
}

func CustomDmenu(prompt string, dmenu []string, isHkeyList bool) string {
    inputFile := "/tmp/rofi_hkey.dmenulist"
    rl, _ := os.OpenFile(inputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    defer rl.Close()

    for _, entry := range dmenu {
        rl.WriteString(entry + "\n")
    }

    var dmenuLines string
    if len(dmenu) < 15 {
        dmenuLines = strconv.Itoa(len(dmenu))
    } else {
        dmenuLines = "15"
    }

    cmd := "rofi -dmenu -i -input " + inputFile + " -p '" + prompt + "' -l " + dmenuLines + " -theme-str 'entry { placeholder: \"\"; } inputbar { children: [prompt, textbox-prompt-colon, entry]; }'" + MenuMessage + "; rm " + inputFile
    output, err := exec.Command("bash", "-c", cmd).Output()
    if err != nil {
        log.Fatal(err)
        os.Exit(1)
    }

    if isHkeyList {
    hkey := strings.Split(string(output), ":")[0]
    return strings.Trim(hkey, "'")
    } else {
    return strings.TrimSuffix(string(output), "\n")
    }
}

func MessageBox(message string) {
    cmd := exec.Command("rofi", "-e", message)
    err := cmd.Run()
    if err != nil {
        log.Fatal(err)
        os.Exit(1)
    }
}
