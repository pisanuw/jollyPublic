
#include <sstream>
// global variable, used to make tests easier to write
stringstream SS;

/**
 * print OK or ERR, comparing the two given parameters
 * optional message parameter also printed to identify test
 * This version works when data types are the same
 * @param valueReturnedByAFunction
 * @param expectedValue
 * @param message optional message
 */
template<typename T>
void isOK(const T &got, const T &expected, string msg = "") {
  // cout << "Got: " << got << ", expected: " << expected << ", msg: " << msg << endl;
  if (got == expected) {
    if (msg == "")
      cout << "OK: got expected value: " << got << endl;
    else
      cout << "OK: " << msg << endl;
  } else {
    if (msg != "")
      cout << "ERR: " << msg << endl;
    else
      cout << "ERR: Test Failed" << endl;
    cout << "    Got   " << got << "\n expected " << expected << endl;
  }
}

// print OK or ERR, works for string and char*
// anything in quotes, such as "abc", defaults to char*
// and has to be explicitly converted
void isOK(const string &str, const char *cstr, string msg = "") {
  isOK(str, string(cstr), msg);
}

// print OK or ERR, works for stringstream and anything else
// convenience function
// ALSO resets global variable simplestream SS
// not the best programming practice, but useful for tests
template<typename T>
void isOK(const stringstream &ss, const T &expected, string msg = "") {
  isOK(ss.str(), string(expected), msg);
  SS.str("");
}

void testJolly() {
   vector<int> v;
   v.push_back(10);
   v.push_back(30);
   v.push_back(20);
   v.push_back(50);
   v.push_back(40);
   v.push_back(60);
   selectionSortVector(v);
   isOK(v[0], 10);
   isOK(v[1], 20);
   isOK(v[2], 30);
   isOK(v[3], 40);
   isOK(v[4], 50);
   isOK(v[5], 60, "vector sorted");
   string car = "car";
   string care = "care";
   string deer = "deer";
   isOK(stringCompare(car, car), 0, "== string equal");
   isOK(stringCompare(car, care), -1, "< string equal");
   isOK(stringCompare(care, car), 1, "> string equal");
   isOK(stringCompare(car, deer), -1, "-1 car deer string equal");
   isOK(stringCompare(deer, car), 1, "deer car string equal");
   int x = 10;
   x = add1(x);
   isOK(x, 11, "add1");
   x = 10;
   add5(x);
   isOK(x, 15, "add5");
   x = 10;
   add10(&x);
   isOK(x, 20, "add10");      
}

int main() {
  testJolly();
  return 0;
}
