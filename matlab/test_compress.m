
all_lo = {
  64 127  0
  64  94 0
  64 127 34
  }';

all_hi = {
  64 64 64
  0 34 0
  127 127 94
  }';

close all

for i=1:numel(all_lo)
  lo = all_lo{i};
  hi = all_hi{i};
  
  x = linspace(0, 127, 127);
  
  y = compress(x, lo, hi, 127);
  subplot(3, 3, i);
  h = plot(x, y);
  set(h, 'LineWidth', 2)
  set(gca, 'XTick', [0, 127])
  set(gca, 'YTick', [0, 127])
  
  axis tight; axis equal
  axis([0 127 0 127]);
  title(sprintf('lo=%.0f, hi=%.0f', lo, hi))
  if ismember(i, [7 8 9])
    xlabel('input value')
  end
  if ismember(i, [1 4 7])
    ylabel('output value')
  end
end

print -dpng compress_example.png