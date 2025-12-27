The checksum calculation for a GGA message (and all other NMEA 0183 sentences) is based on a **Bitwise XOR (Exclusive OR)** operation.

The checksum ensures that the data was not corrupted during transmission (e.g., due to electrical noise or serial buffer overflows).

---

### 1. The Rules of the Calculation
1.  **The Range:** You calculate the XOR sum of every character **between** (but not including) the `$` and the `*`.
2.  **The Input:** You use the ASCII values of the characters.
3.  **The Result:** The final result is a **2-character Hexadecimal string**.

---

### 2. Step-by-Step Walkthrough
Let's use a shortened version of a GGA string for clarity:
`$GPGGA,123519,4807.03,N*47`

**Characters to process:** `G`, `P`, `G`, `G`, `A`, `,`, `1`, `2`, `3`, `5`, `1`, `9`, `,`, `4`, `8`, `0`, `7`, `.`, `0`, `3`, `,`, `N`

**The Math:**
1.  Start with `0`.
2.  `0` XOR 'G' (ASCII 71) = 71
3.  `71` XOR 'P' (ASCII 80) = 23
4.  `23` XOR 'G' (ASCII 71) = 80
5.  ...and so on for every character until the `N`.

The final decimal result for this specific string is **71**. 
In Hexadecimal, **71 decimal = 47 hex**.
Thus, the checksum is `47`.

---

### 3. Logic Table (XOR Review)
The XOR operation follows these rules per bit:
*   `0 ^ 0 = 0`
*   `0 ^ 1 = 1`
*   `1 ^ 0 = 1`
*   `1 ^ 1 = 0`

---

### 4. Implementation Example (Python)
If you are writing code to verify or generate a GGA checksum, here is how you would do it:

```python
def calculate_nmea_checksum(sentence):
    # 1. Remove the $ and the * (and everything after *)
    # Example input: $GPGGA,123519,4807.03,N*47
    data = sentence.split('*')[0] # Get part before *
    if data.startswith('$'):
        data = data[1:]          # Remove $

    checksum = 0
    # 2. Loop through each character and XOR
    for char in data:
        checksum ^= ord(char)

    # 3. Convert to 2-digit Hex (uppercase)
    return hex(checksum)[2:].upper().zfill(2)

# Test
msg = "GPGGA,123519,4807.03,N"
print(f"Calculated Checksum: {calculate_nmea_checksum(msg)}") 
# Output: 47
```

---

### 5. Implementation Example (C/C++)
This is commonly used in Arduino or embedded GPS projects:

```c
char checkSum(char *s) {
    int c = 0;
    // Skip the $ if it exists
    if (*s == '$') s++;
    
    // Process until the * or the end of string
    while (*s != '*' && *s != '\0') {
        c ^= *s++;
    }
    return c;
}
```

### Why does it use XOR?
*   **Efficiency:** XOR is a very "cheap" operation for a CPU/Microcontroller to perform.
*   **Error Detection:** If a single bit in the message changes (a 0 becomes a 1), the XOR result will change significantly, alerting the receiver that the data is invalid. However, it is not perfect—it cannot detect errors if two identical bits in the same position across different characters are flipped (though this is rare in serial communication).