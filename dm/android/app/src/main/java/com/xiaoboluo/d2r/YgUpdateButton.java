package com.xiaoboluo.d2r;

import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.MotionEvent;
import android.view.View;

// 엽굵 모드판: 캐릭터 선택 화면(게임 밖)에서만 왼쪽 위에 뜨는 "업데이트" 버튼.
// 디아2 기본 버튼처럼 어두운 돌 바탕 + 금색 테두리·글자를 코드로 그린다(게임 그림 파일은 쓰지 않음).
// 누르면 최신 릴리스 페이지를 브라우저로 연다. 인터넷 권한이 필요 없다.
final class YgUpdateButton extends View {
    static final String URL = "https://github.com/kakario777-netizen/d2r-mobile/releases/latest";
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG), edge = new Paint(Paint.ANTI_ALIAS_FLAG),
            inner = new Paint(Paint.ANTI_ALIAS_FLAG), text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF box = new RectF();
    private final float dp;
    private boolean pressed;
    private final Runnable poll = new Runnable() {
        @Override public void run() {
            boolean show = DmActivity.nativeInGame() == 0;
            setVisibility(show ? VISIBLE : GONE);
            postDelayed(this, 500);
        }
    };

    YgUpdateButton(Context c) {
        super(c);
        dp = c.getResources().getDisplayMetrics().density;
        edge.setStyle(Paint.Style.STROKE); edge.setStrokeWidth(2 * dp); edge.setColor(0xFF8A6D3B);
        inner.setStyle(Paint.Style.STROKE); inner.setStrokeWidth(1 * dp); inner.setColor(0xFF3A2E1E);
        text.setColor(0xFFC7B377); text.setTextAlign(Paint.Align.CENTER);
        text.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD)); text.setTextSize(15 * dp);
        text.setShadowLayer(2 * dp, 1 * dp, 1 * dp, 0xFF000000);
        setVisibility(GONE);
    }

    void start() { removeCallbacks(poll); post(poll); }
    void stop() { removeCallbacks(poll); }

    @Override protected void onSizeChanged(int w, int h, int ow, int oh) {
        fill.setShader(new LinearGradient(0, 0, 0, h, 0xFF2E2822, 0xFF14110E, Shader.TileMode.CLAMP));
    }

    @Override protected void onDraw(Canvas c) {
        float w = getWidth(), h = getHeight(), r = 3 * dp;
        box.set(dp, dp, w - dp, h - dp);
        c.drawRoundRect(box, r, r, fill);
        if (pressed) c.drawColor(0x40000000);
        c.drawRoundRect(box, r, r, edge);
        box.inset(3 * dp, 3 * dp);
        c.drawRoundRect(box, r, r, inner);
        float y = h / 2 - (text.descent() + text.ascent()) / 2 + (pressed ? dp : 0);
        c.drawText("업데이트", w / 2, y, text);
    }

    @Override public boolean onTouchEvent(MotionEvent e) {
        switch (e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN: pressed = true; invalidate(); return true;
            case MotionEvent.ACTION_CANCEL: pressed = false; invalidate(); return true;
            case MotionEvent.ACTION_UP:
                pressed = false; invalidate();
                if (e.getX() >= 0 && e.getY() >= 0 && e.getX() <= getWidth() && e.getY() <= getHeight()) {
                    try { getContext().startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(URL))); } catch (Exception ignored) { }
                }
                return true;
        }
        return true;
    }
}
