#include <Python.h>
#include <wiringPi.h>
#include <stdio.h>
#include <sys/time.h>
#include <math.h>


//reads a DHT sensor, trying to avoid reading it during an OS interrupt
//so as to decrease the likelihood of an incorrect/incomplete reading.


//maximum number of bits we can read
int nbits=50;

// returns time in seconds after initial call or reset time
double timer(int reset){
    static long secs = 0, usecs=0;
    struct timeval time;
    
    gettimeofday(&time,NULL);
    
    //if this is the first call (or we request a reset), store the time
    if (secs == 0 || reset == 1) {
        secs = time.tv_sec;
        usecs= time.tv_usec;
    }
    
    //subtract the stored time from the measured time
    return (double)(time.tv_sec-secs) + 0.000001 * (double) (time.tv_usec - usecs);
}


int readDHT(int pin, int class, double *temp, double *hum)
{
  //set up GPIO using broadcomm GPIO numbers
  wiringPiSetupGpio() ;
  
  //request high priority from OS
  piHiPri(99);
  
  //set pin to output and high
  pinMode (pin, OUTPUT) ;
  digitalWrite(pin,1);
  

  double t1, t2;
  
  
  double data[nbits];
  
  
  t1=timer(1);
  t2=timer(0);
  
  //pause but keep CPU under high load to stop scheduling 
  //This tricks the OS to giving us priority as it thinks we're busy
  while(t2-t1 < 0.02){
      t2=timer(0);
  }
  
  
  // Now send the signal to say we want the DHT to read:
  // sleep for 18ms (at least) and determine
  // when the 10ms interrupt is (if possible).
  // to do this we look for large time intervals between
  // successive iterations of the a the timing loop, and find the
  // intervals that are spaced by ~10ms 
  
  digitalWrite(pin,0);
  
  int i=0;
  int counter=0;
  
  //allow up to 20 high values. We will look through them later
  double highdt[20];
  
  double tlast;
  t1=timer(0);
  t2=timer(0);
  tlast=timer(0);
  
  //during the sleep, we identify any times where the time between
  // each iteration is > 20us
  while(t2-t1 < 0.020){
      t2=timer(0);
      if (t2-tlast > 0.000020){
          if (counter<20) highdt[counter] = t2;
          counter++;
      }
      tlast=t2;
  }
  
  
  // we now go through this list and find entries that are 10ms apart
  // if we find them, then we have the 10ms interval :)
  double dum;
  int j,success;
  success=0;
  for (j=0;j<counter;j++){
      for (i=j;i<counter;i++){
          dum = highdt[i]-highdt[j];
          if (dum > 0.009 && dum < 0.011){
              success=1;
              break;
          }
      }
      if (success == 1) break;
  }    
  
  // Define the time we want to release the signal so the DHT sends data
  // (This is set so that we release just after a OS interrupt, so we
  // *hopefully* have ~10ms of relatively uninterrupted CPU time to take
  // accurate timing measurements)
  double target_time;
  if (success == 0) {
      target_time=0;
  } else {
      target_time=highdt[i]+0.011;
  }
  
  // wait until we think an interrupt has just happened
  t2=timer(0);
  while (t2 < target_time){
      t2=timer(0);
  }
  
  //now we go!
  
  pinMode(pin,INPUT);
  
  int old=0;
  int new;
  int count=0;
  t1=timer(0);
  t2=timer(0);
  //poll the pin for 8ms
  // if the pin has gone low, record the time this happened as the times
  // between these lows correspond to the bits being sent
  while ((t2-t1)<0.008){
      t2=timer(0);
      new=digitalRead(pin);
      if (new-old == -1){
          if (count >= nbits) break;
          data[count] = t2;
          count+=1;
      }
      old=new;
  }
  
  pinMode(pin,OUTPUT);
  digitalWrite(pin,1);
  
  //set the priority back to normal
  piHiPri(0);


  //see if we have recorded the right number of times (41 or 42)
  
  if (count == 41 || count == 42) {
      //construct array of 40 bits
      int bits[40];
      int offset;
      // we only want the last 41 measurements, so if 42 we measure from
      // measurement 2
      if (count == 41) {offset=0;} else {offset=1;}
      for (i=0;i<40;i++){
          // interval of <100us is a 0, >100us is a 1
          if ((data[i+1+offset]-data[i+offset])*1e6 < 100){
              bits[i]=0;
          } else {
              bits[i]=1;
          }
          //printf("#%d: %d\n",i,bits[i]);
      }
      
      //construct array of 5 bytes from the 40 bits
      int bytes[5];
      int byte;
      i=0;
      for (byte=0;byte<5;byte++){
          bytes[byte]=0;
          for (i=0;i<8;i++){
              bytes[byte] |= (bits[i+8*byte]<<(7-i));
          }
      }
      
      //checksum
      if (((bytes[0]+bytes[1]+bytes[2]+bytes[3])&bytes[4]) != bytes[4]){
          printf("Checksum failed \n");
          printf("details: sum= %d, reference= %d\n",(bytes[0]+bytes[1]+bytes[2]+bytes[3])&bytes[4], bytes[4]);
          return 2;
      }
      
      if (class == 22) {
          *hum = (double)((bytes[0]<<8) + bytes[1]);
          *hum = *hum/10.;
          
          *temp = (double)((bytes[2]<<8) + bytes[3]);
          *temp = *temp/10.;
          // see if the temperature is negative
          if ((bytes[2]&128) != 0) *temp = -1. * *temp;
      } else {
          *hum = (double)bytes[0];
          *temp = (double)bytes[2];
      }
      printf("Temp = %3.1f 'C, hum= %3.1f %%\n",*temp,*hum);
      
      
      
      
   }else{
       printf("Incorrect number of bits: %d\n",count);
       for (i=0;i<count;i++){
         printf("i=%d, t=%f\n",i,data[i]);
       }
       return 1;
   }
   

  return 0 ;
}

// function called if we're calling from python
static PyObject* DHTC_read(PyObject *self, PyObject *args){

  int pin, class;
 
  double temp,hum;
  
  
  //parse the arguments
  if (PyArg_ParseTuple(args,"ii",&pin,&class)){
    //check that the values in are sensible:
    if (pin < 0 || pin > 27) {
        printf("Error: The selected pin number %d is invalid\n",pin);
        return NULL;
    }
    if (class != 22 && class != 11){
        printf("Error: Invalid DHT class %d. Should be 11 or 22.\n",class);
        return NULL;
    }
  } else {
    printf("Error: C unable to parse python input\n");
    return NULL;
  }

  int result;
  
  result=readDHT(pin,class,&temp,&hum);
  
  if (result == 0){
      return Py_BuildValue("{s:i,s:d,s:d}","status",result,"Temperature",temp,"Humidity",hum);
  } else {
      return Py_BuildValue("{s:i,s:O,s:O}","status",result,"Temperature",Py_None,"Humidity",Py_None);
  }

  
  
}

static PyMethodDef DHTC_funcs[] = {
  {"read", (PyCFunction)DHTC_read, METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initDHTC(void) {
  Py_InitModule("DHTC", DHTC_funcs);
  Py_InitModule3("DHTC", DHTC_funcs,"C library that reads a DHT sensor");
}


int main(int argc, char **argv){
    if (argc != 3){
        printf("Usage: ./DHT [GPIO pin number] [class (11 or 22)]\n");
        return 10;
    }
    
    int pin,class, result;
    double temp, hum;
    
    // parse pin argument
    pin=atoi(argv[1]);
    
    class=atoi(argv[2]);
    if (class != 11 && class != 22) {
        printf("Error: Invalid DHT class\nMust be 11 or 22\n");
        return 10;
    }
    
    printf("Reading from GPIO pin %2d\n",pin);
    result = readDHT(pin,class,&temp,&hum);

    return result;
}
