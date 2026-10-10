import cv2
import easyocr
import os

img_path = "..\\uploads\\processed\\9999\\page_1\\00_original.png"
out_dir = "C:\\Users\\black man\\.gemini\\antigravity-ide\\brain\\e21073d1-8097-46df-86b9-7d5c6a2dffa3\\scratch\\crops"
os.makedirs(out_dir, exist_ok=True)

reader = easyocr.Reader(['ar'], gpu=False)
image = cv2.imread(img_path)

horizontal_list, free_list = reader.detect(image)

boxes = []
if horizontal_list and len(horizontal_list) > 0:
    for bbox in horizontal_list[0]:
        x_min, x_max, y_min, y_max = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        y_min = max(0, y_min - 5)
        y_max = min(image.shape[0], y_max + 5)
        x_min = max(0, x_min - 5)
        x_max = min(image.shape[1], x_max + 5)
        boxes.append((x_min, y_min, x_max, y_max))

# Sort bounding boxes properly by overlapping lines
# Calculate y-center for each box
boxes_with_centers = [(b, (b[1] + b[3]) / 2) for b in boxes]

# Sort purely by top coordinate first
boxes_with_centers.sort(key=lambda x: x[0][1])

lines_grouped = []
current_line = []
current_line_y_max = -1

for b, yc in boxes_with_centers:
    if current_line_y_max == -1:
        current_line.append(b)
        current_line_y_max = b[3]
    else:
        # If the center of this box is above the y_max of the current line, it belongs to the same line
        if yc < current_line_y_max:
            current_line.append(b)
            current_line_y_max = max(current_line_y_max, b[3])
        else:
            lines_grouped.append(current_line)
            current_line = [b]
            current_line_y_max = b[3]

if current_line:
    lines_grouped.append(current_line)

# Now sort each line right-to-left
final_boxes = []
for line in lines_grouped:
    line.sort(key=lambda b: -b[0]) # right to left
    final_boxes.extend(line)

for idx, b in enumerate(final_boxes[:30]):
    crop = image[b[1]:b[3], b[0]:b[2]]
    cv2.imwrite(os.path.join(out_dir, f"crop_{idx:02d}.png"), crop)

print(f"Saved {min(10, len(boxes))} crops to {out_dir}")
