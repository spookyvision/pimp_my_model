//
//  MyModel.m
//  example

#import "MyModel.h"


@implementation MyModel
@synthesize someItems, text, count;



-(void) dealloc {

    [someItems release];

    [text release];
    [super dealloc];
}



-(id) initWithSomeItems: (NSArray*) inSomeItems text: (NSString*) inText count: (int) inCount {
    
    if (self = [super init]) {
             self.someItems = inSomeItems;
             self.text = inText;
             self.count = inCount;

    }
    
    return self;
}
    
@end
