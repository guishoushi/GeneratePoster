from progress.bar import IncrementalBar
import time

bar = IncrementalBar('Processing:', max=100)
for i in range(20):
    time.sleep(0.1)  # 模拟耗时操作
    bar.next()
bar.finish()