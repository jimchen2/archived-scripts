#include<stdio.h>
#include<stdlib.h>
#include<windows.h>
#include<time.h>
#include<graphics.h>
#include<conio.h>

#pragma warning(default: 4996)
//this is for compiling the mousehit function
//that can not be used
#pragma comment(lib,"Winmm.lib")
//this is for music
IMAGE mount;
IMAGE home;
IMAGE unknown;
IMAGE city;
IMAGE page;
IMAGE find;
IMAGE starting;
IMAGE enemy;
IMAGE deadcity;
//all the images needed
MOUSEMSG m;
LOGFONT f;
//f is supposed to be the font 
//which I use to set the font the same

void generals();
//starting program
void move(int x2, int y2, int x3, int y3);
//this is for moving armies
void go();
//this is for going
void kbhit000();
//tying in characters
void printf000();
//print the map
void startup000();
//startup game
void goup000();
//a function for increasing the armies
void mouse000();
void landgoup();
void castlegoup();
void count();
void jim();
void music();
// function for music
void settings();
void setname();
//set user name
void a2048();
void replay2();
//watch replay
void aiplay();
//computer play the game
void move2(int, int, int, int);
void go2();
//computer move and go
void move3(int, int, int, int);


int M = 20, N = 10;
//map width and height
int t = 25, unset = 1;
double singletime = 0.5;
//the single time for a turn
int a[100][100], b[100][100];
//map type
int aa[100][100][10000], bb[100][100][10000];
//replay
int px = 1, py = 1;
//this i sfor moving the armies
int i, j, k, turn = 1, lastturn = 0, landturn = 0;
int cit = 20, mountain = 5;
int setnam = 0;
char s[1000], username[10] = "Anonymous", ti[1000], u[1000];
double uptime = 0, begintime = 0, up2 = 0;
double be2 = 0, up3 = 0, be3 = 0, timeagain = 0, be4 = 0, be5 = 0, be8 = 0;
int lastturn1 = 0, lastturn2 = 0, lastturn3 = 0, score = 0, land111 = 0, score2 = 0, land222 = 0;
char input;
double xxx = 1;
int xx1[1000], xx2[1000], xx3[1000], xx4[1000];
//stack for moving armies
int kk1[1000000], kk2[1000000], kk3[1000000], kk4[1000000];
//move armies for computer
int enx, eny, ax, ay;


void main()
{
startgame:
	initgraph(1280, 605);
	BeginBatchDraw();
	loadimage(&page, "res\\1.png", 1280, 604, TRUE);
	putimage(0, 0, &page);
	settextstyle(50, 30, "华文行楷");
	setbkmode(TRANSPARENT);
	int ksk1, ksk2, ksk3;
	srand(time(NULL));
	ksk1 = rand() % 256; ksk2 = rand() % 256; ksk3 = rand() % 256;
	settextcolor(RGB(ksk1, ksk3, ksk2));
	outtextxy(0, 0, "music");
	settextcolor(BLACK);
	settextstyle(23, 13, "arial");
	if (setnam == 1)	outtextxy(565, 300, username);
	else outtextxy(565, 300, "Anonymous");
	settextcolor(WHITE);
	settextstyle(50, 30, "宋体");
	FlushBatchDraw();
	while (1)
	{
		if (MouseHit())
		{
			m = GetMouseMsg();
			if (m.uMsg == WM_LBUTTONDOWN) {
				if ((m.x >= (int)1280 * 851 / 1920.0) && (m.x <= (int)1280 * 1069 / 1920.0) && (m.y >= (int)604 * 542 / 906.0) && (m.y <= (int)604 * 613 / 906.0))
				{
					generals();
					goto startgame;
				}
				if ((m.x - 1244) * (m.x - 1244) + (m.y - 34) * (m.y - 34) < 901)
				{
					replay2();
					goto startgame;
				}
				if (m.x < 175 && m.y < 35)
				{
					music();
					goto startgame;
				}
				if ((m.x - 1240) * (m.x - 1240) + (m.y - 105) * (m.y - 105) < 801)
				{
					settings();
					goto startgame;
				}
				if ((m.x - 1242) * (m.x - 1242) + (m.y - 178) * (m.y - 178) < 1089)
				{
					jim();
					goto startgame;
				}
				if (m.x > 495 && m.x < 784 && m.y>293 && m.y < 325)
				{
					setname();
					goto startgame;
				}
			}

		}


	}

}



void generals()
{
	startup000();
	while (1) {
		aiplay();
		printf000();
		goup000();
		kbhit000();
		int win = 0;
		for (i = 1; i <= M; i++)for (j = 1; j < N; j++)if (b[i][j] == -1 && a[i][j] > 0)
		{
			setfillcolor(WHITE);
			solidrectangle(t * M / 2 + t, t * N / 2 + t, 3 * t * M / 2 + 3 * t, 3 * t * N / 2 + 3 * t);
			settextcolor(BLACK);
			settextstyle(3 * t, 3 * t / 5, NULL);
			outtextxy(t * M / 2 + 3 * t, t * N + 2 * t, "You Win");
			FlushBatchDraw();
			up3 = clock();
			while ((clock() - up3) / CLOCKS_PER_SEC < 2);
			input = 27; goto jjj;
		}
		for (i = 1; i <= M; i++)for (j = 1; j < N; j++)if (b[i][j] == 3 && a[i][j] < 0)
		{
			setfillcolor(WHITE);
			solidrectangle(t * M / 2 + t, t * N / 2 + t, 3 * t * M / 2 + 3 * t, 3 * t * N / 2 + 3 * t);
			settextcolor(BLACK);
			settextstyle(3 * t, 3 * t / 5, NULL);
			outtextxy(t * M / 2 + 3 * t, t * N + 2 * t, "You Lost");
			FlushBatchDraw();
			up3 = clock();
			while ((clock() - up3) / CLOCKS_PER_SEC < 2);
			input = 27; goto jjj;
		}
		if (input == 27)
		{

			setfillcolor(WHITE);
			solidrectangle(t * M / 2 + t, t * N / 2 + t, 3 * t * M / 2 + 3 * t, 3 * t * N / 2 + 3 * t);
			settextcolor(BLACK);
			settextstyle(3 * t, (3 * t) / 5, NULL);
			outtextxy(t * M / 2 + 3 * t, t * N + 2 * t, "You Lost");
			FlushBatchDraw();
			up3 = clock();
			while ((clock() - up3) / CLOCKS_PER_SEC < 2);
		jjj:
			input = 0; break;
		}
		go();
		mouse000();
		//sprintf_s(s, "%d", t);
		//outtextxy(0, 200, s);
		FlushBatchDraw();
	}
	EndBatchDraw();
	closegraph();
}
void aiplay()
{
	int i1, i2;
	int per = rand() % 4; int ert = rand() % M; int ekt = rand() % N; int sett = rand() % 3;
	for (i1 = 1; i1 <= M; i1++)for (i2 = 1; i2 <= N; i2++)if (a[i1][i2] < -1)
	{
		if (per == 0) { move2(i1, i2, i1, i2 + 1); if (sett == 0)move3(i1, i2, i1, i2 + 1); else move2(i1, i2, i1, i2 + 1); }
		if (per == 1) { move2(i1, i2, i1, i2 - 1); if (sett == 0)move3(i1, i2, i1, i2 - 1);	else	move2(i1, i2, i1, i2 - 1); }
		if (per == 2) {
			move2(i1, i2, i1 + 1, i2); if (sett == 0)move3(i1, i2, i1 + 1, i2); else move2(i1, i2, i1 + 1, i2);
		}
		if (per == 3) {
			move2(i1, i2, i1 - 1, i2); if (sett == 0)move2(i1, i2, i1 - 1, i2); else move3(i1, i2, i1 - 1, i2);
		}
	}
	go2();
}
void move2(int x11, int y11, int x22, int y22)
{

	if (x22 > 0 && x22 <= M && y22 > 0 && y22 <= N && x11 > 0 && y11 > 0 && x11 <= M && y11 <= N && a[x22][y22] == 0)
		if (b[x22][y22] != 1 && b[x22][y22] != 6 && b[x22][y22] != 2 && b[x22][y22] != 4 && b[x22][y22] != 5)
			if (b[x11][y11] != 1 && b[x11][y11] != 6 && b[x11][y11] != 2 && b[x11][y11] != 4 && b[x11][y11] != 5)
			{
				for (i = 0; kk1[i] != 0; i++);		kk1[i] = x11;
				for (i = 0; kk2[i] != 0; i++);		kk2[i] = y11;
				for (i = 0; kk3[i] != 0; i++);		kk3[i] = x22;
				for (i = 0; kk4[i] != 0; i++);		kk4[i] = y22;
			}
}
void move3(int x11, int y11, int x22, int y22)
{

	if (x22 > 0 && x22 <= M && y22 > 0 && y22 <= N && x11 > 0 && y11 > 0 && x11 <= M && y11 <= N)
		if (b[x22][y22] != 1 && b[x22][y22] != 6 && b[x22][y22] != 2 && b[x22][y22] != 4 && b[x22][y22] != 5)
			if (b[x11][y11] != 1 && b[x11][y11] != 6 && b[x11][y11] != 2 && b[x11][y11] != 4 && b[x11][y11] != 5)
			{
				for (i = 0; kk1[i] != 0; i++);		kk1[i] = x11;
				for (i = 0; kk2[i] != 0; i++);		kk2[i] = y11;
				for (i = 0; kk3[i] != 0; i++);		kk3[i] = x22;
				for (i = 0; kk4[i] != 0; i++);		kk4[i] = y22;
			}
}
void go2()
{
	if (-a[kk1[0]][kk2[0]] > 1 && b[kk1[0]][kk2[0]] != 1 && b[kk1[0]][kk2[0]] != 6 && b[kk1[0]][kk2[0]] != 2 && b[kk1[0]][kk2[0]] != 4 && b[kk1[0]][kk2[0]] != 5 && b[kk3[0]][kk4[0]] != 1 && b[kk3[0]][kk4[0]] != 6 && b[kk3[0]][kk4[0]] != 2 && b[kk3[0]][kk4[0]] != 4 && b[kk3[0]][kk4[0]] != 5)
	{
		if ((clock() - be8) / CLOCKS_PER_SEC > singletime)
		{
			a[kk3[0]][kk4[0]] = a[kk3[0]][kk4[0]] + a[kk1[0]][kk2[0]] + 1;
			a[kk1[0]][kk2[0]] = -1;
			be8 = clock();
			for (i = 0; i < 9999; i++)
			{
				kk1[i] = kk1[i + 1];
				kk2[i] = kk2[i + 1];
				kk3[i] = kk3[i + 1];
				kk4[i] = kk4[i + 1];
			}
		}
	}
	else
	{
		for (i = 0; i < 9999; i++)
		{
			kk1[i] = kk1[i + 1];
			kk2[i] = kk2[i + 1];
			kk3[i] = kk3[i + 1];
			kk4[i] = kk4[i + 1];
		}
	}
}
void kbhit000()
{
	if (_kbhit())
	{
		input = _getch();
		if (input == 'a') { move(px, py, px - 1, py); }
		if (input == 'w') { move(px, py, px, py - 1); }
		if (input == 's') { move(px, py, px, py + 1); }
		if (input == 'd') { move(px, py, px + 1, py); }
		if (input == 'q') {
			for (i = 0; i <= 999; i++) { xx1[i] = 0; xx2[i] = 0; xx3[i] = 0; xx4[i] = 0; }
		}

		if (input == 27) { return; }
	}

}
void move(int x11, int y11, int x22, int y22)
{

	if (x22 > 0 && x22 <= M && y22 > 0 && y22 <= N && b[x22][y22] != 5 && b[x22][y22] != 6)
	{
		if (b[x22][y22] != 1)
		{
			px = x22;
			py = y22;
			ax = x22;
			ay = y22;
			for (i = 0; xx1[i] != 0; i++);		xx1[i] = x11;
			for (i = 0; xx2[i] != 0; i++);		xx2[i] = y11;
			for (i = 0; xx3[i] != 0; i++);		xx3[i] = x22;
			for (i = 0; xx4[i] != 0; i++);		xx4[i] = y22;
		}
	}

}
void go()
{
	if (a[xx1[0]][xx2[0]] > 1)
	{
		if ((clock() - be3) / CLOCKS_PER_SEC > singletime)
		{
			a[xx3[0]][xx4[0]] += a[xx1[0]][xx2[0]] - 1;
			a[xx1[0]][xx2[0]] = 1;
			be3 = clock();
			for (i = 0; i < 999; i++)
			{
				xx1[i] = xx1[i + 1];
				xx2[i] = xx2[i + 1];
				xx3[i] = xx3[i + 1];
				xx4[i] = xx4[i + 1];
			}
		}
	}
	else
	{
		for (i = 0; i < 999; i++)
		{
			xx1[i] = xx1[i + 1];
			xx2[i] = xx2[i + 1];
			xx3[i] = xx3[i + 1];
			xx4[i] = xx4[i + 1];
		}
	}
}
void replay2()
{
	closegraph();
	initgraph(M * (2 * t) + (4 * t), N * (2 * t) + (4 * t));
	BeginBatchDraw();
	settextstyle(t, 2 * t / 5, "宋体");
	settextstyle(&f);
	settextstyle(t, 2 * t / 5, NULL);

	int turn2 = turn; turn = 1;
	while (turn <= turn2)
	{
		if ((clock() - be5) / CLOCKS_PER_SEC > singletime)
		{
			for (i = 1; i <= M; i++) for (j = 1; j <= N; j++)
			{
				if (bb[i][j][turn] == 5)bb[i][j][turn] = 1;
				if (bb[i][j][turn] == 6)bb[i][j][turn] = 2;
				if (bb[i][j][turn] == -2)bb[i][j][turn] = -1;
				if (bb[i][j][turn] == 200)bb[i][j][turn] = 0;
				if (bb[i][j][turn] == 100)bb[i][j][turn] = 0;


			}
			setbkmode(TRANSPARENT);
			setfillcolor(BLACK);
			solidrectangle(0, 0, 3000, 3000);
			setfillcolor(RGB(200, 200, 200));

			solidrectangle(t + t, t + t, M * (2 * t) + t + t, N * (2 * t) + t + t);
			setlinecolor(WHITE);
			for (i = 0; i <= M; i++) line((2 * t) * i + 2 * t, 2 * t, (2 * t) * i + t + t, N * (2 * t) + t + t);
			for (j = 0; j <= N; j++) line(2 * t, (2 * t) * j + 2 * t, M * (2 * t) + 2 * t, (2 * t) * j + 2 * t);

			setfillcolor(RGB(58, 95, 205));
			for (i = 1; i <= M; i++) {
				for (j = 1; j <= N; j++) {
					if (aa[i][j][turn] > 0) {
						solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
					}

				}
			}
			setfillcolor(RGB(200, 200, 200));
			for (i = 1; i <= M; i++) {
				for (j = 1; j <= N; j++) {
					if (b[i][j] == 100) {
						solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
					}
				}
			}
			setfillcolor(RGB(255, 0, 0));
			for (i = 1; i <= M; i++) {
				for (j = 1; j <= N; j++) {
					if (aa[i][j][turn] < 0) {
						if (bb[i][j][turn] != 5 && bb[i][j][turn] != 6 && bb[i][j][turn] != -2 && bb[i][j][turn] != 200)
							solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
					}

				}
			}
			for (i = 1; i <= M; i++) {
				for (j = 1; j <= N; j++)
				{
					if (bb[i][j][turn] == 0)
					{
						if (aa[i][j][turn] != 0)
						{
							sprintf_s(s, "%d", abs(aa[i][j][turn])); outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
						}
					}
					if (bb[i][j][turn] == 100)
					{

						if (aa[i][j][turn] < 0) { sprintf_s(s, "%d", abs(aa[i][j][turn])); outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s); }
					}
					else if (bb[i][j][turn] == 1)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &mount);
					}
					else if (bb[i][j][turn] == 2)
					{
						if (aa[i][j][turn] > 0)		putimage(i * t * 2 + 1, j * t * 2 + 1, &city);
						else	putimage(i * t * 2 + 1, j * t * 2 + 1, &deadcity);
						sprintf_s(s, "%d", abs(aa[i][j][turn]));
						outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);

					}
					else if (bb[i][j][turn] == 3)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &home);
						sprintf_s(s, "%d", aa[i][j][turn]);
						outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
					}
					else if (bb[i][j][turn] == -1)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &enemy);
						sprintf_s(s, "%d", abs(aa[i][j][turn]));
						outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
					}
					else if (bb[i][j][turn] == 4)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &city);
						sprintf_s(s, "%d", abs(aa[i][j][turn]));
						outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
					}
					else if (bb[i][j][turn] == 5)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &unknown);
					}
					else if (bb[i][j][turn] == 6)
					{
						putimage(i * t * 2 + 1, j * t * 2 + 1, &unknown);
					}

				}
				printf("\n");
			}

			setlinecolor(RGB(200, 200, 200));
			setlinestyle(PS_SOLID, 2);
			for (i = 1; i <= M; i++)for (j = 1; j <= N; j++)if (b[i][j] == 2 && a[i][j] > 0)b[i][j] = 4;
			printf("\n");
			turn++; be5 = clock();
			sprintf(s, "turn:%d", turn / 2);
			outtextxy(0, 0, s);
			FlushBatchDraw();
		}
	}
}
void printf000()
{
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] == 5 || b[i][j] == 6) {
				if (a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0)b[i][j] -= 4;
			}
			if (b[i][j] == -2)
			{
				if (a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0)b[i][j] = -1;
			}
			if (b[i][j] == 200)
				if (a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0)b[i][j] = 100;
			if (b[i][j] == 100)
				if (a[i][j] > 0)b[i][j] = 0;
			if (b[i][j] == 0)
				if (!(a[i][j] > 0))b[i][j] = 100;
			if (b[i][j] == 100)
				if (!(a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0))b[i][j] = 200;

		}
	}
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] == 1 || b[i][j] == 2) {
				if (!(a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0))b[i][j] += 4;
			}
			if (b[i][j] == -1)
			{
				if (!(a[i + 1][j] > 0 || a[i][j + 1] > 0 || a[i - 1][j] > 0 || a[i][j - 1] > 0 || a[i + 1][j + 1] > 0 || a[i - 1][j - 1] > 0 || a[i + 1][j - 1] > 0 || a[i - 1][j + 1] > 0))b[i][j] = -2;
			}
		}
	}
	setbkmode(TRANSPARENT);
	setfillcolor(BLACK);
	solidrectangle(0, 0, 3000, 3000);
	setfillcolor(RGB(57, 57, 57));

	solidrectangle(t + t, t + t, M * (2 * t) + t + t, N * (2 * t) + t + t);
	setfillcolor(RGB(58, 95, 205));
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (a[i][j] > 0) {
				solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
			}

		}
	}
	setfillcolor(RGB(200, 200, 200));
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] == 100) {
				solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
			}
		}
	}
	gettextstyle(&f);
	setfillcolor(RGB(255, 0, 0));
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (a[i][j] < 0) {
				if (b[i][j] != 5 && b[i][j] != 6 && b[i][j] != -2 && b[i][j] != 200)
					solidrectangle((2 * t) * i + 2, (2 * t) * j + 2, (2 * t) * i + 2 * t - 2, (2 * t) * j + 2 * t - 2);
			}

		}
	}
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++)
		{
			if (b[i][j] == 0)
			{
				sprintf_s(s, "%d", abs(a[i][j])); outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
			}
			if (b[i][j] == 100)
			{
				if (a[i][j] < 0) { sprintf_s(s, "%d", abs(a[i][j])); outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s); }
			}
			else if (b[i][j] == 1)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &mount);
			}
			else if (b[i][j] == 2)
			{
				if (a[i][j] > 0)		putimage(i * t * 2 + 1, j * t * 2 + 1, &city);
				else	putimage(i * t * 2 + 1, j * t * 2 + 1, &deadcity);
				sprintf_s(s, "%d", abs(a[i][j]));
				outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);

			}
			else if (b[i][j] == 3)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &home);
				sprintf_s(s, "%d", a[i][j]);
				outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
			}
			else if (b[i][j] == -1)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &enemy);
				sprintf_s(s, "%d", abs(a[i][j]));
				outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
			}
			else if (b[i][j] == 4)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &city);
				sprintf_s(s, "%d", abs(a[i][j]));
				outtextxy(i * (2 * t) + t - (int)(0.25 * strlen(s) * t), j * (2 * t) + t / 2, s);
			}
			else if (b[i][j] == 5)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &unknown);
			}
			else if (b[i][j] == 6)
			{
				putimage(i * t * 2 + 1, j * t * 2 + 1, &unknown);
			}

		}
		printf("\n");
	}
	/*setlinecolor(WHITE);
	for (i = 0; i <= M; i++) line((2 * t) * i + 2 * t, 2 * t, (2 * t) * i + t + t, N * (2 * t) + t + t);
	for (j = 0; j <= N; j++) line(2 * t, (2 * t) * j + 2 * t, M * (2 * t) + 2 * t, (2 * t) * j + 2 * t);
	*/
	setlinecolor(RGB(200, 200, 200));
	setlinestyle(PS_SOLID, 2);
	rectangle(px * (2 * t) + 1, py * (2 * t) + 1, px * (2 * t) + (2 * t - 1), py * (2 * t) + (2 * t - 1));
	for (i = 1; i <= M; i++)for (j = 1; j <= N; j++)if (b[i][j] == 2 && a[i][j] > 0)b[i][j] = 4;
	//sprintf_s(s, "%f", (clock() - begintime) / CLOCKS_PER_SEC);
	//outtextxy(0, 0, s);
	settextstyle(t, (int)(0.4 * t), NULL);
	outtextxy(0, t * N, "music");
	count();
}
void startup000() {
	if (N <= 2 && M <= 6)t = 100;
	else if (N <= 5 && M <= 14)t = 50;
	else if (N <= 13 && M <= 28)t = 25;
	else if (N <= 18 && M <= 36)t = 20;
	else if (N >= 19 || M >= 37)  t = (800 / (M + 2) > 400 / (N + 2)) ? (400 / (N + 2) - 1) : (800 / (M + 2) - 1);
	loadimage(&city, "res\\8.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&deadcity, "res\\5.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&mount, "res\\2.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&home, "res\\3.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&unknown, "res\\4.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&enemy, "res\\7.png", 2 * t - 2, 2 * t - 2, true);
	loadimage(&find, "res\\f.png", 1280, 618);
	loadimage(&starting, "res\\s.png", 1280, 609);
	uptime = clock();
	turn = 1;
	setfillcolor(BLACK);
	solidrectangle(0, 0, 3000, 3000);
	putimage(0, 0, &find);
	FlushBatchDraw();
	while ((clock() - uptime) / CLOCKS_PER_SEC < 1)
	{
		if (MouseHit())
		{
			m = GetMouseMsg();
			if (m.uMsg == WM_LBUTTONDOWN)
			{
				if (m.x > 724 && m.x < 812 && m.y>207 && m.y < 240)
				{
					input = 27; return;
				}
			}
		}
	}
	uptime = clock();
	solidrectangle(0, 0, 3000, 3000);
	putimage(0, 0, &starting);
	FlushBatchDraw();
	while ((clock() - uptime) / CLOCKS_PER_SEC < 1);
	solidrectangle(0, 0, 3000, 3000);
	for (i = 0; i < 55; i++)for (j = 0; j <= 55; j++) { a[i][j] = 0; b[i][j] = 0; }
	begintime = clock(); be2 = clock();
	turn = 1;
	closegraph();
	for (i = 0; i <= 999; i++) { xx1[i] = 0; xx2[i] = 0; xx3[i] = 0; xx4[i] = 0; }
	for (i = 0; i <= 999999; i++) { kk1[i] = 0; kk2[i] = 0; kk3[i] = 0; kk4[i] = 0; }

	initgraph(M * (2 * t) + (4 * t), N * (2 * t) + (4 * t));

	settextstyle(t, (int)t * 0.4, NULL);
	setbkcolor(RGB(80, 80, 80));
	setfillcolor(RGB(57, 57, 57));
	cleardevice();
	solidrectangle(0, 0, 3000, 3000);
	int kkk1, kkk2;
	srand(time(NULL));
	kkk1 = rand() % M + 1; kkk2 = rand() % N + 1;
	b[kkk1][kkk2] = 3; a[kkk1][kkk2] = 1;
	px = kkk1; py = kkk2;

	kkk1 = rand() % M + 1; kkk2 = rand() % N + 1;
	if (b[kkk1][kkk2] == 3)
	{
		if (M != 2 * kkk1 + 1)
		{
			b[M - kkk1 + 1][kkk2] = -1;
			a[M - kkk1 + 1][kkk2] = -1;
			enx = M - kkk1 + 1;
			eny = kkk2;
		}
		else
		{
			b[1][kkk2] = -1;
			a[M - kkk1 + 1][kkk2] = -1;
			enx = 1;
			eny = kkk2;
		}
	}
	b[kkk1][kkk2] = -1;
	a[kkk1][kkk2] = -1;
	enx = kkk1;
	eny = kkk2;
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] != 3 && b[i][j] != -1)
			{
				if (rand() % cit == 0)b[i][j] = 2;
				else if (rand() % (mountain * (cit - 1)) < cit)b[i][j] = 1;
			}
		}
	}
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] == 2)a[i][j] = -50 + rand() % 11;
		}
	}
	for (i = 1; i <= M; i++) {
		for (j = 1; j <= N; j++) {
			if (b[i][j] == 1)b[i][j] = 5;
			if (b[i][j] == 2)b[i][j] = 6;
			if (b[i][j] == -1)b[i][j] = -2;
		}
	}
}
void goup000()
{
	landgoup();
	castlegoup(); ;
}
void mouse000()
{
	int dddd, eeee;
	while (MouseHit())
	{
		m = GetMouseMsg();
		if (m.uMsg == WM_LBUTTONDOWN)
		{
			dddd = (m.x) / (2 * t);
			eeee = (m.y) / (2 * t);
			if (dddd > 0 && dddd <= M && eeee > 0 && eeee <= N)
			{
				if (px == dddd && py == eeee + 1 || px == dddd && py == eeee - 1 || px == dddd + 1 && py == eeee || px == dddd - 1 && py == eeee)move(px, py, dddd, eeee);
				px = dddd; py = eeee;
			}
			if (m.x >= 0 && m.x <= 2 * t && m.y >= t * N && m.y <= t * N + t)
			{
				music();
			}
		}
	}
}
void landgoup()
{

	if ((clock() - up3) / CLOCKS_PER_SEC >= 50 * singletime) {
		up3 = clock();
		for (i = 1; i <= M; i++) {
			for (j = 1; j <= N; j++)
			{
				if (b[i][j] == 0 || b[i][j] == 100 || b[i][j] == 200)
				{
					if (a[i][j] >= 1)a[i][j]++;
					if (-a[i][j] >= 1)a[i][j]--;
				}


			}
		}
	}

}
void castlegoup()
{
	if ((clock() - up2) / CLOCKS_PER_SEC >= 2 * singletime)
	{
		up2 = clock();
		for (i = 1; i <= M; i++) {
			for (j = 1; j <= N; j++)
			{
				if (b[i][j] == 4)
				{
					a[i][j]++;
				}
				if (b[i][j] == 3)
				{
					a[i][j]++;
				}
				if (b[i][j] == -1 || b[i][j] == -2)
				{
					a[i][j]--;
				}
			}
		}
	}
}
void count() {
	if ((clock() - timeagain) / CLOCKS_PER_SEC > singletime)
	{
		turn++;		timeagain = clock();

	}
	score = 0; land111 = 0; score2 = 0; land222 = 0;
	for (i = 1; i <= M; i++)for (j = 1; j <= N; j++) { if (a[i][j] > 0) { land111++; score += a[i][j]; if (b[i][j] == 2)score++; } }
	int k = M * 2 * t - t * 6 - 100;
	settextstyle(t, (2 * t) / 5, NULL);
	sprintf(s, "%s:", username);
	outtextxy(k, 0, s);
	sprintf(s, "%10d%10d", score - 1, land111);
	outtextxy(k + 4 * t, 0, s);
	for (i = 1; i <= M; i++)for (j = 1; j <= N; j++) { {if (a[i][j] < 0 && b[i][j] != 6 && b[i][j] != 2) { land222++; score2 = score2 - a[i][j]; }} }
	sprintf(s, "%s:", "Player 2");
	outtextxy(k, t, s);
	sprintf(s, "%10d%10d", score2 - 1, land222);
	outtextxy(k + 4 * t, t, s);
	sprintf(s, "turn:%d", turn / 2);
	outtextxy(0, 0, s);
	for (i = 1; i <= M; i++)for (j = 1; j <= N; j++)
	{
		aa[i][j][turn] = a[i][j];
		bb[i][j][turn] = b[i][j];
	}
}
void jim()
{
	solidrectangle(0, 0, 3000, 3000);
	closegraph();
	initgraph(1280, 640);
	BeginBatchDraw();
	while (1)
	{
		settextstyle(50, 30, "宋体");
		outtextxy(30, 0, "陈加木 ");
		outtextxy(30, 100, "学号：PB21000002");
		outtextxy(30, 200, "2020级上海交大附中    致远英才班");
		outtextxy(30, 300, "2021级中国科学技术大学 少年班学院");
		if (_kbhit())
		{
			input = getch();
			if (input == 27) { input = 0; return; }
		}
		if (MouseHit())
		{
			m = GetMouseMsg();
			if (m.uMsg == WM_LBUTTONDOWN)
			{
				if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)	return;
				if (m.x > 50 && m.x < 180 && m.y>390 && m.y < 490)a2048();
			}
		}
		rectangle(1160, 560, 1240, 600);
		settextstyle(25, 10, NULL);
		outtextxy(1160 + 20, 560 + 10, "BACK");
		rectangle(50, 390, 180, 490);
		settextstyle(20, 10, NULL);
		outtextxy(60 + 10, 360 + 60, "2048 Game");
		FlushBatchDraw();

	}
	EndBatchDraw();
	closegraph();
}
void music()
{
	closegraph();
	initgraph(1280, 640);
	BeginBatchDraw();
	settextstyle(25, 10, NULL);

	int page = 111;
	while (1)
	{
		setfillcolor(BLACK);
		solidrectangle(0, 0, 3000, 3000);
		if (page == 111)
		{
			outtextxy(30, 0, "Ed Sheeran ");
			outtextxy(30, 40, "One Direction");
			outtextxy(30, 80, "Westlife");
			outtextxy(30, 120, "Taylor Swift");
			outtextxy(30, 160, "Maroon 5");
			outtextxy(30, 200, "Chainsmokers");
			outtextxy(30, 240, "One Republic");
			outtextxy(30, 280, "Phantom of the Opera");
			outtextxy(30, 320, "Les Miserables");
			outtextxy(30, 360, "City of Stars");
			outtextxy(30, 400, "Frozen");
			outtextxy(30, 440, "Despacito");
			for (i = 40; i <= 480; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			rectangle(60, 560, 140, 600);
			outtextxy(60 + 20, 560 + 20, "MUTE");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
					{
						input = 0;
						settextstyle(t, (int)t * 0.4, NULL);
						setfillcolor(RGB(57, 57, 57));

						solidrectangle(0, 0, 3000, 3000);
						return;
					}
					if (m.y < 480)
					{
						page = 1 + m.y / 40;
					}
					if (m.x > 60 && m.x <= 140 && m.y > 560 && m.y <= 600)
					{
						mciSendString("close m", NULL, 0, NULL);
					}
				}
			}
		}
		if (page == 1)
		{
			outtextxy(30, 0, "Shape of You");
			outtextxy(30, 40, "Perfect");
			outtextxy(30, 80, "Photograph");
			outtextxy(30, 120, "Thinking Out Loud");
			outtextxy(30, 160, "Shivers");
			outtextxy(30, 200, "Castle on the Hill");
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Shapeofyou.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Perfect.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Photograph.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Thinkingoutloud.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Shivers.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Castleonthehill.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}

			for (i = 40; i <= 240; i += 40)line(0, i, 1280, i);
		}
		if (page == 2)
		{
			outtextxy(30, 0, "What Makes You Beautiful");
			outtextxy(30, 40, "Best Song Ever");
			outtextxy(30, 80, "Drag Me Down");
			outtextxy(30, 120, "One Thing");
			outtextxy(30, 160, "You and I");
			outtextxy(30, 200, "Steal My Girl");
			outtextxy(30, 240, "Night Changes");
			for (i = 40; i <= 280; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Whatmakesyoubeautiful.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Bestsongever.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Dragmedown.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Onething.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\Youandi\.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Stealmygirl.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Nightchanges.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 3)
		{
			outtextxy(30, 0, "If I Let You Go ");
			outtextxy(30, 40, "My Love");
			outtextxy(30, 80, "Nothing's Gonna Change My Love For You");
			outtextxy(30, 120, "Seasons in the Sun");
			outtextxy(30, 160, "Swear It Again");
			outtextxy(30, 200, "Uptown Girl");
			outtextxy(30, 240, "You Raise Me up");
			for (i = 40; i <= 280; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\.Ifiletyougomp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Mylove.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Nothingsgonnachange.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Seasonsinthesun.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Swearitagain.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Uptowngirl.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Youraisemeup.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 4)
		{
			outtextxy(30, 0, "Begin Again");
			outtextxy(30, 40, "Blank Space");
			outtextxy(30, 80, "Cardigan");
			outtextxy(30, 120, "Enchanted");
			outtextxy(30, 160, "Gorgeous");
			outtextxy(30, 200, "I don't wanna live forever");
			outtextxy(30, 240, "I Knew You were Trouble");
			outtextxy(30, 280, "Last Christmas");
			outtextxy(30, 320, "Love Story");
			outtextxy(30, 360, "Lover");
			for (i = 40; i <= 400; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			settextstyle(20, 8, NULL);
			outtextxy(1160 - 60, 560 + 20, "DOWN");
			settextstyle(25, 10, NULL);

			rectangle(1160 - 60, 560, 1160 - 20, 600);

			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					if (m.x > 1100 && m.x < 1140 && m.y>559 && m.y < 601)
						page = 44;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Beginagain.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Blankspace.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Cardigan.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Enchanted.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Gorgeous.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Idontwanna.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Iknewyouweretrouble.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 8:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Lastchristmas.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 9:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Lovestory.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 10:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Lover.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 44)
		{
			outtextxy(30, 0, "Red");
			outtextxy(30, 40, "Santa Baby");
			outtextxy(30, 80, "Shake it off");
			outtextxy(30, 120, "Sparks Fly");
			outtextxy(30, 160, "Style");
			outtextxy(30, 200, "We are Never Ever Getting Back Together");
			outtextxy(30, 240, "Welcome to New York");
			outtextxy(30, 280, "Wildest Dreams");
			outtextxy(30, 320, "Willow");
			outtextxy(30, 360, "You Belong With Me");
			outtextxy(1160 - 60, 560 + 20, "UP");
			for (i = 40; i <= 400; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			rectangle(1160 - 60, 560, 1160 - 20, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");

			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					if (m.x > 1100 && m.x < 1140 && m.y>559 && m.y < 601)
						page = 4;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Red.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Santababy.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Shakeitoff.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Sparksfly.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Style.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Wearenever.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Welcometonewyork.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 8:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Wildestdreams.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 9:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Willow.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 10:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Youbelongwithme.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}

			}
		}
		if (page == 5)
		{
			outtextxy(30, 0, "Animals");
			outtextxy(30, 40, "Feelings");
			outtextxy(30, 80, "Lost Stars");
			outtextxy(30, 120, "Maps");
			outtextxy(30, 160, "Memories");
			outtextxy(30, 200, "Moves like jagger");
			outtextxy(30, 240, "One More Night");
			outtextxy(30, 280, "Sugar");
			for (i = 40; i <= 320; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");

			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Animals.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Feelings.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Loststars.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Maps.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Memories.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Moveslikejagger.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Onemorenight.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 8:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Sugar.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 6)
		{
			outtextxy(30, 0, "All we know");
			outtextxy(30, 40, "Closer");
			outtextxy(30, 80, "Don't let me down");
			outtextxy(30, 120, "Pains");
			outtextxy(30, 160, "Roses");
			outtextxy(30, 200, "Sick boy");
			outtextxy(30, 240, "Something just like this");
			for (i = 40; i <= 280; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Allweknow.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Closer.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Dontletme.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Pains.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Roses.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Sickboy.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Somethingjustlikethis.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 7)
		{
			outtextxy(30, 0, "Apologize");
			outtextxy(30, 40, "Counting Stars");
			outtextxy(30, 80, "I lived");
			outtextxy(30, 120, "Kids");
			outtextxy(30, 160, "Love runs out");
			outtextxy(30, 200, "Rescue Me");
			for (i = 40; i <= 240; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Apologize.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Countingstars.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Ilived.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Kids.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Loverunsout.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Rescueme.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 8)
		{
			outtextxy(30, 0, "Phantom of the Opera");
			outtextxy(30, 40, "Think of Me");
			outtextxy(30, 80, "The Mirror");
			outtextxy(30, 120, "Angel of Music");
			outtextxy(30, 160, "All I Ask of You");
			outtextxy(30, 200, "Wishing you Were Somehow Here Again");
			outtextxy(30, 240, "The Point of No Return");
			outtextxy(30, 280, "Music of the Night");
			for (i = 40; i <= 320; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\PTO.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Thinkofme.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Themirror.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Angelofmusic.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Alliaskofyou.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Wishingyouwere.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Thepointofnoreturn.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 8:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Musicofthenight.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 9)
		{
			outtextxy(30, 0, "I Dreamed a Dream");
			outtextxy(30, 40, "Castle on a Cloud");
			outtextxy(30, 80, "Look Down");
			outtextxy(30, 120, "Who am I");
			outtextxy(30, 160, "The Confrontation");
			outtextxy(30, 200, "At the End of the Day");
			outtextxy(30, 240, "One Day More");
			outtextxy(30, 280, "On My Own");
			for (i = 40; i <= 320; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Idreamedadream.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Castleonacloud.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Lookdown.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Whoami.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Theconfrontation.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Atthe.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 7:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Onedaymore.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 8:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Onmyown.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 10)
		{
			outtextxy(30, 0, "City of Stars");
			outtextxy(30, 40, "Mia and Sebastian's Theme");
			for (i = 40; i <= 80; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Cityofstars.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Mia.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 11)
		{
			outtextxy(30, 0, "Let it Go");
			outtextxy(30, 40, "Do you Want to Build a Snowman");
			outtextxy(30, 80, "Into the Unknown");
			outtextxy(30, 120, "All is Found");
			outtextxy(30, 160, "For the First Time in Forever");
			outtextxy(30, 200, "Love is an Open Door");
			for (i = 40; i <= 240; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
					int k = m.y / 40 + 1;
					switch (k)
					{
					case 1:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Letitgo.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 2:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Doyouwant.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 3:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Intotheunknown.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 4:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Allisfoud.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 5:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Forthefirst.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					case 6:
						mciSendString("close m", NULL, 0, NULL);
						mciSendString("open res\\Loveisanopendoor.mp3 alias m", NULL, 0, NULL);
						mciSendString("play m", NULL, 0, NULL);
						break;
					}
				}
			}
		}
		if (page == 12)
		{
			outtextxy(30, 0, "Despacito");
			for (i = 40; i <= 40; i += 40)line(0, i, 1280, i);
			rectangle(1160, 560, 1240, 600);
			outtextxy(1160 + 20, 560 + 20, "BACK");
			if (MouseHit())
			{
				m = GetMouseMsg();
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
						page = 111;
				}
				int k = m.y / 40 + 1;
				switch (k)
				{
				case 1:
					mciSendString("close m", NULL, 0, NULL);
					mciSendString("open res\\Despacito.mp3 alias m", NULL, 0, NULL);
					mciSendString("play m", NULL, 0, NULL);
					break;
				}
			}
		}

		if (_kbhit())
		{
			input = getch();
			if (input == 27)
			{
				input = 0;
				closegraph();
				initgraph(M * (2 * t) + (4 * t), N * (2 * t) + (4 * t));
				settextstyle(t, (int)t * 0.4, NULL);
				setbkcolor(RGB(80, 80, 80));
				setfillcolor(RGB(57, 57, 57));

				cleardevice();
				solidrectangle(0, 0, 3000, 3000);

				return;
			}
		}

		FlushBatchDraw();
	}
	EndBatchDraw();
	closegraph();
}
void settings()
{
	unset = 0;
	setfillcolor(BLACK);
	setbkcolor(BLACK);
	cleardevice();
	solidrectangle(0, 0, 3000, 3000);
	BeginBatchDraw();
	while (1)
	{
		solidrectangle(0, 0, 3000, 3000);
		settextstyle(35, 16, NULL);
		settextcolor(WHITE);
		outtextxy(30, 0, "Game Speed");
		outtextxy(30, 100, "Width");
		outtextxy(30, 200, "Height");
		outtextxy(30, 300, "City Density");
		outtextxy(30, 400, "Mountain Density");
		if (xxx < 1)
		{
			sprintf(s, "%.2lfx", xxx);
			outtextxy(300, 0, s);
		}
		if (xxx >= 1)
		{
			sprintf(s, "%dx", (int)xxx);
			outtextxy(300, 0, s);
		}
		sprintf(s, "%d", M);
		outtextxy(180, 100, s);
		sprintf(s, "%d", N);
		outtextxy(180, 200, s);
		sprintf(s, "1/%d", cit);
		outtextxy(300, 300, s);
		sprintf(s, "1/%d", mountain);
		outtextxy(300, 400, s);
		setlinestyle(NULL, 1);
		line(50, 50, 1050, 50);
		line(50, 250, 1050, 250);
		line(50, 350, 1050, 350);
		line(50, 450, 1050, 450);
		line(50, 150, 1050, 150);
		setlinestyle(NULL, 10);
		setlinecolor(GREEN);
		line(M * 20 + 50, 150 - 15, M * 20 + 50, 150 + 15);
		line(N * 40 + 50, 250 - 15, N * 40 + 50, 250 + 15);
		line(2000 / cit + 50, 350 - 15, 2000 / cit + 50, 350 + 15);
		line(2000 / mountain + 50, 450 - 15, 2000 / mountain + 50, 450 + 15);
		if (xxx >= 1)		line((int)550 + 500 * (xxx - 1) / 9, 50 - 15, (int)550 + 500 * (xxx - 1) / 9, 50 + 15);
		if (xxx < 1)		line((int)550 + 5000 * (xxx - 1) / 9, 50 - 15, (int)550 + 5000 * (xxx - 1) / 9, 50 + 15);
		setlinecolor(WHITE);
		settextstyle(20, 10, NULL);
		outtextxy(30, 70, "0.1x");
		outtextxy(30, 170, "0");
		outtextxy(30, 270, "0");
		outtextxy(30, 370, "low");
		outtextxy(30, 470, "low");
		outtextxy(550, 70, "1x");
		outtextxy(1080, 70, "10x");
		outtextxy(1080, 170, "50");
		outtextxy(1080, 270, "25");
		outtextxy(1080, 370, "high");
		outtextxy(1080, 470, "high");

		if (_kbhit())
		{
			input = getch();
			if (input == 27)
			{
				input = 0;
				singletime = 1 / (2 * xxx);
				setbkcolor(RGB(80, 80, 80));
				cleardevice();
				return;
			}
		}
		if (MouseHit())
		{

			m = GetMouseMsg();
			if (m.uMsg == WM_LBUTTONDOWN)
			{
				if (m.x >= 50 && m.x <= 1055 && m.y >= 35 && m.y <= 65)
				{
					int mx = 9 * (m.x - 550);
					mx = mx / 50 + 100;
					xxx = mx / 100.0;
					//xxx = ((int)100 * ((m.x - 550) * 9.0 / 5500.0 + 1.0)) / 100.0;
				}
				if (m.x >= 550 && m.x <= 1050 && m.y >= 35 && m.y <= 65)
				{
					int mx = (m.x - 550) * 9;
					xxx = mx / 500.0 + 1;

					//xxx = (int)((m.x - 550) * 9 / 500.0 + 1);
				}
				if (m.x >= 110 && m.x <= 1055 && m.y >= 135 && m.y <= 165)
				{
					M = (m.x - 50) / 20;
				}
				if (m.x >= 170 && m.x <= 1055 && m.y >= 235 && m.y <= 265)
				{
					N = (m.x - 50) / 40;
				}
				if (m.x >= 51 && m.x <= 1055 && m.y >= 335 && m.y <= 365)
				{
					cit = (int)2000.0 / (m.x - 50);
				}
				if (m.x >= 51 && m.x <= 1055 && m.y >= 435 && m.y <= 465)
				{
					mountain = (int)2000.0 / (m.x - 50);
				}
				if (m.uMsg == WM_LBUTTONDOWN)
				{
					if (m.x > 1159 && m.x < 1241 && m.y>559 && m.y < 601)
					{
						singletime = 1 / (2 * xxx);
						setbkcolor(RGB(80, 80, 80));
						cleardevice();
						return;

					}
				}
			}
		}
		rectangle(1160, 560, 1240, 600);
		settextstyle(25, 10, NULL);
		outtextxy(1160 + 10, 560 + 10, "BACK");
		FlushBatchDraw();
	}
	EndBatchDraw();
	closegraph();
}
void setname()
{
	memset(s, '\0', 1000);
	memset(ti, '\0', 1000);
	setnam = 1;
	double timtime = clock();
	while (1)
	{
		setfillcolor(WHITE);
		solidrectangle(400, 200, 880, 450);
		settextstyle(30, 12, "等线");
		settextcolor(BLACK);
		outtextxy(420, 220, "     Choose your username carefully");
		setlinecolor(BLACK);
		rectangle(450, 390, 830, 440);
		rectangle(450, 300, 830, 350);
		setlinecolor(WHITE);
		outtextxy(450, 400, "    Set Username");
		if (_kbhit())
		{
			if (strlen(s) <= 10)
			{
				input = _getch();
				s[strlen(s)] = input;
				if (input == 27) { input = 0; memcpy(username, s, 10); return; }
			}
		}
		i = (2 * clock() - 2 * timtime) / CLOCKS_PER_SEC;
		if (i % 2 == 0)
		{
			sprintf(ti, "%s", s);
		}
		else
		{
			sprintf(ti, "%s |", s);
		}
		outtextxy(450, 300, ti);

		if (MouseHit())
		{
			m = GetMouseMsg();
			if (m.uMsg == WM_LBUTTONDOWN) {
				if ((m.x >= 450) && (m.x <= 830) && (m.y >= 390) && (m.y <= 440))
				{
					memcpy(username, s, 10); return;
				}
			}
		}
		FlushBatchDraw();
	}
}






void a2048()
{
	double sc, ec = 0; sc = (double)clock() / CLOCKS_PER_SEC;
	int a2048[4][4] = { 2 };
	int i, j, k = 0, x, sign = 0, rnd, move = 0, y = 0, over, continue1 = 0;
	char input = '/0', timeuse[20];
	int number;
music:	mciSendString("close all", NULL, 0, NULL);
	srand((unsigned)time(NULL));
	number = 1 + (rand() % 5);
	if (number == 1) { mciSendString("open res\\Whatmakesyoubeautiful.mp3", NULL, 0, NULL); mciSendString("play res\\Whatmakesyoubeautiful.mp3 repeat", NULL, 0, NULL); }
	if (number == 2) { mciSendString("open res\\Bestsongever.mp3", NULL, 0, NULL); mciSendString("play res\\Bestsongever.mp3 repeat", NULL, 0, NULL); }
	if (number == 3) { mciSendString("open res\\Nightchanges.mp3", NULL, 0, NULL); mciSendString("play res\\Nightchanges.mp3 repeat", NULL, 0, NULL); }
	if (number == 4) { mciSendString("open res\\Dragmedown.mp3", NULL, 0, NULL); mciSendString("play res\\Dragmedown.mp3 repeat", NULL, 0, NULL); }
	if (number == 5) { mciSendString("open res\\Onething.mp3", NULL, 0, NULL); mciSendString("play res\\Onething.mp3 repeat", NULL, 0, NULL); }
	initgraph(960, 700);
	BeginBatchDraw();
	setbkcolor(WHITE);
	cleardevice();
	while (1)
	{
	again:continuegame:
		over = 1;
		settextstyle(50, 25, "宋体");
		settextcolor(BLACK);
		outtextxy(50, 0, "2048 Game");
		settextstyle(40, 20, "华文行楷");
		settextcolor(GREEN);
		outtextxy(50, 100, "designed by Jim  2021.11");
		settextstyle(40, 20, "华文彩云");
		settextcolor(BROWN);
		outtextxy(50, 160, "Press w,a,s,d to move");
		settextstyle(25, 12, "华文彩云");
		settextcolor(BLACK);
		outtextxy(500, 0, "1 to change music, 2 to mute");
		outtextxy(500, 25, "0 to end game");
		outtextxy(500, 50, "Esc to return");
		setlinestyle(PS_SOLID | PS_ENDCAP_FLAT, 3);
		setlinecolor(BLACK);
		sign = 0;
		settextstyle(50, 25, "黑体");
		settextcolor(BLACK);
		setfillcolor(YELLOW);
		solidrectangle(50, 300, 850, 620);
		line(50, 300, 850, 300);
		line(50, 380, 850, 380);
		line(50, 460, 850, 460);
		line(50, 540, 850, 540);
		line(50, 620, 850, 620);
		line(50, 300, 50, 620);
		line(250, 300, 250, 620);
		line(450, 300, 450, 620);
		line(650, 300, 650, 620);
		line(850, 300, 850, 620);
		for (i = 0; i <= 3; i++)for (j = 0; j <= 3; j++) {
			if (a2048[i][j] == 2) outtextxy(100 + j * 200, 320 + i * 80, "2");
			if (a2048[i][j] == 4) outtextxy(100 + j * 200, 320 + i * 80, "4");
			if (a2048[i][j] == 8) outtextxy(100 + j * 200, 320 + i * 80, "8");
			if (a2048[i][j] == 16) outtextxy(100 + j * 200, 320 + i * 80, "16");
			if (a2048[i][j] == 32)outtextxy(100 + j * 200, 320 + i * 80, "32");
			if (a2048[i][j] == 64) outtextxy(100 + j * 200, 320 + i * 80, "64");
			if (a2048[i][j] == 128) outtextxy(100 + j * 200, 320 + i * 80, "128");
			if (a2048[i][j] == 256) outtextxy(100 + j * 200, 320 + i * 80, "256");
			if (a2048[i][j] == 512) outtextxy(100 + j * 200, 320 + i * 80, "512");
			if (a2048[i][j] == 1024) outtextxy(100 + j * 200, 320 + i * 80, "1024");
			if (a2048[i][j] == 2048) outtextxy(100 + j * 200, 320 + i * 80, "2048");
			if (a2048[i][j] == 2048) outtextxy(100 + j * 200, 320 + i * 80, "2048");
			if (a2048[i][j] == 4096) outtextxy(100 + j * 200, 320 + i * 80, "4096");
			if (a2048[i][j] == 8192) outtextxy(100 + j * 200, 320 + i * 80, "8192");
			if (a2048[i][j] == 16384) outtextxy(100 + j * 200, 320 + i * 80, "16384");
			if (a2048[i][j] == 32768) outtextxy(100 + j * 200, 320 + i * 80, "32768");
		}
		if (continue1 == 0) {
			for (i = 0; i <= 3; i++) { for (j = 0; j <= 3; j++) { if (a2048[i][j] == 2048)sign = 1; } }if (sign == 1) {
				setfillcolor(WHITE);
				solidrectangle(0, 0, 960, 700);
				settextstyle(50, 25, "楷书");
				settextcolor(GREEN);
				Sleep(1000);
				outtextxy(50, 0, "Congratulations!");
				outtextxy(50, 100, "I love C Programming Language!");
				settextstyle(50, 25, "华文彩云");
				settextcolor(BLACK);
				outtextxy(50, 300, "Press 1 to continue");
				FlushBatchDraw();
				if (_kbhit) {
					input = _getch();
					if (input == '1') {
						continue1 = 1;
						setfillcolor(WHITE);
						solidrectangle(0, 0, 960, 700);
						goto continuegame;
					}
					if (input == 27)
					{
						input = 0; setbkcolor(RGB(80, 80, 80)); setbkmode(TRANSPARENT); initgraph(1280, 640); return;
					}
				}
				break;
			}
		}
		for (i = 0; i <= 3; i++) { for (j = 0; j <= 3; j++) { if (a2048[i][j] == 0)over = 0; } }
		for (i = 0; i <= 3; i++) { for (j = 0; j <= 2; j++) { if (a2048[i][j] == a2048[i][j + 1])over = 0; } }
		for (i = 0; i <= 3; i++) { for (j = 0; j <= 2; j++) { if (a2048[j][i] == a2048[j + 1][i])over = 0; } }
		if (over) {
		endgame:
			setfillcolor(WHITE);
			solidrectangle(0, 0, 959, 699);
			settextstyle(50, 25, "楷书");
			settextcolor(RED);
			outtextxy(50, 0, "Gameover");
			settextstyle(50, 25, "华文彩云");
			outtextxy(50, 100, "Press 1 to try again");
			FlushBatchDraw();
			if (_kbhit) {
				input = _getch();
				if (input == '1') {
					setfillcolor(WHITE);
					solidrectangle(0, 0, 960, 700);
					for (i = 0; i <= 3; i++)for (j = 0; j <= 3; j++)a2048[i][j] = 0; a2048[0][0] = 2;
					sc = (double)clock() / CLOCKS_PER_SEC;
					goto again;
				}
				if (input == 27)
				{
					input = 0; setbkcolor(RGB(80, 80, 80)); setbkmode(TRANSPARENT); initgraph(1280, 640); return;
				}
			}
			break;
		}
		FlushBatchDraw();
		if (_kbhit())
		{
			input = _getch(); move = 0;
			if (input == '1')goto music; back:
			if (input == '2')mciSendString("close all", NULL, 0, NULL);
			if (input == '0')goto endgame;
			if (input == 27)
			{
				input = 0; setbkcolor(RGB(80, 80, 80)); setbkmode(TRANSPARENT); initgraph(1280, 640); return;
			}
			if (input == 'a')
			{
				for (i = 0; i <= 3; i++) {
					if (!(((a2048[i][2]) && (a2048[i][1]) && (a2048[i][0])) || ((a2048[i][1]) && (a2048[i][0]) && !(a2048[i][2]) && !(a2048[i][3])) || (!a2048[i][3] && !a2048[i][2] && !a2048[i][1]))) { move = 1; }
					if (a2048[i][0] == 0) { a2048[i][0] = a2048[i][1]; a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][0] == 0) { a2048[i][0] = a2048[i][1]; a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][0] == 0) { a2048[i][0] = a2048[i][1]; a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][1] == 0) { a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][1] == 0) { a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][2] == 0) { a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; }
					if (a2048[i][3] == 0) {
						if ((a2048[i][0] == a2048[i][1]) && (a2048[i][1] != 0)) { a2048[i][0] *= 2; a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; move = 1; }
						else if ((a2048[i][1] == a2048[i][2]) && (a2048[i][2] != 0)) { a2048[i][1] *= 2; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; move = 1; }
					}
					else {
						if (a2048[i][0] == a2048[i][1] && a2048[i][2] == a2048[i][3]) { a2048[i][0] *= 2; a2048[i][1] = 2 * a2048[i][2]; a2048[i][2] = 0; a2048[i][3] = 0; move = 1; }
						else if (a2048[i][0] == a2048[i][1] && a2048[i][2] != a2048[i][3]) { a2048[i][0] *= 2; a2048[i][1] = a2048[i][2]; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; move = 1; }
						else if (a2048[i][0] != a2048[i][1] && a2048[i][2] == a2048[i][1]) { a2048[i][1] *= 2; a2048[i][2] = a2048[i][3]; a2048[i][3] = 0; move = 1; }
						else if (a2048[i][0] != a2048[i][1] && a2048[i][2] == a2048[i][3]) { a2048[i][2] += a2048[i][3]; a2048[i][3] = 0; move = 1; }
					}

				}
			}
			if (input == 'd')
			{
				for (i = 0; i <= 3; i++) {
					if (!((a2048[i][3] && a2048[i][2] && a2048[i][1]) || (!a2048[i][0] && !a2048[i][1] && !a2048[i][2]) || (a2048[i][3] && a2048[i][2] && !a2048[i][0] && !a2048[i][1]))) { move = 1; }
					if (a2048[i][3] == 0) { a2048[i][3] = a2048[i][2]; a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][3] == 0) { a2048[i][3] = a2048[i][2]; a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][3] == 0) { a2048[i][3] = a2048[i][2]; a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][2] == 0) { a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][2] == 0) { a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][1] == 0) { a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; }
					if (a2048[i][0] == 0) {
						if ((a2048[i][3] == a2048[i][2]) && (a2048[i][2] != 0)) { a2048[i][3] *= 2; a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; move = 1; }
						if ((a2048[i][1] == a2048[i][2]) && (a2048[i][2] != 0)) { a2048[i][2] *= 2; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; move = 1; }
					}
					else {
						if (a2048[i][3] == a2048[i][2] && a2048[i][1] == a2048[i][0]) { a2048[i][3] *= 2; a2048[i][2] = 2 * a2048[i][1]; a2048[i][1] = 0; a2048[i][0] = 0; move = 1; }
						else if (a2048[i][3] == a2048[i][2] && a2048[i][1] != a2048[i][0]) { a2048[i][3] *= 2; a2048[i][2] = a2048[i][1]; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; move = 1; }
						else if (a2048[i][3] != a2048[i][2] && a2048[i][2] == a2048[i][1]) { a2048[i][2] *= 2; a2048[i][1] = a2048[i][0]; a2048[i][0] = 0; move = 1; }
						else if (a2048[i][3] != a2048[i][2] && a2048[i][1] == a2048[i][0]) { a2048[i][1] += a2048[i][0]; a2048[i][0] = 0; move = 1; }
					}
				}
			}
			if (input == 'w')
			{
				for (i = 0; i <= 3; i++) {
					if (!((a2048[0][i] && a2048[1][i] && a2048[2][i]) || (!a2048[3][i] && !a2048[1][i] && !a2048[2][i]) || (a2048[0][i] && a2048[1][i] && !a2048[2][i] && !a2048[3][i]))) { move = 1; }
					if (a2048[0][i] == 0) { a2048[0][i] = a2048[1][i]; a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[0][i] == 0) { a2048[0][i] = a2048[1][i]; a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[0][i] == 0) { a2048[0][i] = a2048[1][i]; a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[1][i] == 0) { a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[1][i] == 0) { a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[2][i] == 0) { a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; }
					if (a2048[3][i] == 0) {
						if ((a2048[0][i] == a2048[1][i]) && (a2048[1][i] != 0)) { a2048[0][i] *= 2; a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; move = 1; }
						if ((a2048[1][i] == a2048[2][i]) && (a2048[2][i] != 0)) { a2048[1][i] *= 2; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; move = 1; }
					}
					else {
						if (a2048[0][i] == a2048[1][i] && a2048[2][i] == a2048[3][i]) { a2048[0][i] *= 2; a2048[1][i] = 2 * a2048[2][i]; a2048[2][i] = 0; a2048[3][i] = 0; move = 1; }
						else if (a2048[0][i] == a2048[1][i] && a2048[2][i] != a2048[3][i]) { a2048[0][i] *= 2; a2048[1][i] = a2048[2][i]; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; move = 1; }
						else if (a2048[0][i] != a2048[1][i] && a2048[2][i] == a2048[1][i]) { a2048[1][i] *= 2; a2048[2][i] = a2048[3][i]; a2048[3][i] = 0; move = 1; }
						else if (a2048[0][i] != a2048[1][i] && a2048[2][i] == a2048[3][i]) { a2048[2][i] *= 2; a2048[3][i] = 0; move = 1; }
					}
				}
			}
			if (input == 's')
			{
				for (i = 0; i <= 3; i++) {
					if (!((a2048[3][i] && a2048[1][i] && a2048[2][i]) || (!a2048[0][i] && !a2048[1][i] && !a2048[2][i]) || (!a2048[0][i] && !a2048[1][i] && a2048[2][i] && a2048[3][i]))) { move = 1; }
					if (a2048[3][i] == 0) { a2048[3][i] = a2048[2][i]; a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[3][i] == 0) { a2048[3][i] = a2048[2][i]; a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[3][i] == 0) { a2048[3][i] = a2048[2][i]; a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[2][i] == 0) { a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[2][i] == 0) { a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[1][i] == 0) { a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; }
					if (a2048[0][i] == 0) {
						if ((a2048[3][i] == a2048[2][i]) && (a2048[2][i] != 0)) { a2048[3][i] *= 2; a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; move = 1; }
						if ((a2048[1][i] == a2048[2][i]) && (a2048[2][i] != 0)) { a2048[2][i] *= 2; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; move = 1; }
					}
					else {
						if (a2048[3][i] == a2048[2][i] && a2048[1][i] == a2048[0][i]) { a2048[3][i] *= 2; a2048[2][i] = 2 * a2048[1][i]; a2048[1][i] = 0; a2048[0][i] = 0; move = 1; }
						else if (a2048[3][i] == a2048[2][i] && a2048[1][i] != a2048[0][i]) { a2048[3][i] *= 2; a2048[2][i] = a2048[1][i]; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; move = 1; }
						else if (a2048[3][i] != a2048[2][i] && a2048[2][i] == a2048[1][i]) { a2048[2][i] *= 2; a2048[1][i] = a2048[0][i]; a2048[0][i] = 0; move = 1; }
						else if (a2048[3][i] != a2048[2][i] && a2048[1][i] == a2048[0][i]) { a2048[1][i] += a2048[0][i]; a2048[0][i] = 0; move = 1; }
					}
				}
			}
			if (((input == 'a') || (input == 's') || (input == 'd') || (input == 'w')) && (move)) {
				sign = 0; k = 0; x = 0; rnd = (rand() % 10); if (rnd == 0)rnd = 4; else rnd = 2;
				for (i = 0; i <= 3; i++) { for (j = 0; j <= 3; j++) { if (a2048[i][j] == 0) k++; } }
				x = 1 + rand() % k;
				for (i = 0; i <= 3; i++) { for (j = 0; j <= 3; j++) { if (sign == 0) { if (a2048[i][j] == 0) { x--; if (x == 0) { a2048[i][j] = rnd; sign = 1; } } } } }
			}
		}
		ec = (double)clock() / CLOCKS_PER_SEC;
		y = (int)(ec - sc);
		sprintf_s(timeuse, "%d", y);
		settextcolor(BLACK);
		settextstyle(30, 15, "华文琥珀");
		outtextxy(580, 200, "time:");
		outtextxy(680, 200, timeuse);
		outtextxy(765, 200, "(sec)");
	}
	EndBatchDraw();
	closegraph();

}

