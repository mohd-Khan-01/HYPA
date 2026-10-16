from decode.tools.process_output import OutputCapture


capture = OutputCapture(max_bytes=8)
capture.append(b"hello")
capture.append(b"wor")

assert bytes(capture.data) == b"hellowor"
assert capture.truncated is False
print("Exact limit: PASS")

capture.append(b"ld")
assert bytes(capture.data) == b"hellowor"
assert capture.truncated is True
print("Overflow preserves prefix: PASS")

for _ in range(100):
    capture.append(b"x" * 4096)

assert len(capture.data) == 8
assert capture.text() == "hellowor"
print("Later chunks do not grow retained output: PASS")

other = OutputCapture(max_bytes=8)
other.append(b"stderr")
assert other.text() == "stderr"
assert capture.text() == "hellowor"
print("Independent buffers: PASS")

unicode_capture = OutputCapture(max_bytes=3)
unicode_capture.append("éé".encode("utf-8"))

assert len(unicode_capture.data) == 3
assert unicode_capture.truncated is True
assert unicode_capture.text() == "é\uFFFD"
print("Incomplete UTF-8 tail handled: PASS")